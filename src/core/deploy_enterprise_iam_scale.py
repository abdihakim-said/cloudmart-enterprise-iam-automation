#!/usr/bin/env python3

import boto3
import json
import csv
import argparse
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class ScalableEnterpriseIAMDeployment:
    """Scalable Enterprise IAM Deployment for testing with larger datasets"""
    
    def __init__(self, environment='dev'):
        self.iam = boto3.client('iam')
        self.sts = boto3.client('sts')
        self.environment = environment
        self.account_id = self.sts.get_caller_identity()['Account']
        
        print(f"🏢 Scalable Enterprise IAM Deployment")
        print(f"🌍 Environment: {environment}")
        print(f"📍 AWS Account: {self.account_id}")
    
    def generate_test_users(self, count):
        """Generate test users for scale testing"""
        
        print(f"📋 Generating {count} test users...")
        
        departments = ['engineering', 'data', 'security', 'finance', 'operations', 'product', 'sales', 'marketing']
        roles = {
            'engineering': ['developer', 'senior-engineer', 'devops-engineer'],
            'data': ['data-analyst', 'data-scientist', 'ml-engineer'],
            'security': ['security-analyst', 'security-engineer'],
            'finance': ['financial-analyst', 'budget-manager'],
            'operations': ['operations-manager', 'infrastructure-engineer'],
            'product': ['product-manager', 'business-analyst'],
            'sales': ['sales-rep', 'account-manager'],
            'marketing': ['marketing-analyst', 'content-manager']
        }
        
        users = []
        for i in range(count):
            dept = random.choice(departments)
            role = random.choice(roles[dept])
            
            user = {
                'username': f'testuser{i+1:04d}',
                'department': dept,
                'role': role,
                'manager_email': f'manager{(i//20)+1}@cloudmart.com',
                'start_date': '2024-01-01',
                'access_level': random.choice(['low', 'medium', 'high']),
                'business_justification': f'Scale testing user for {role} in {dept} department - automated test user for enterprise IAM system validation'
            }
            users.append(user)
        
        # Save to CSV
        filename = f'scale_test_users_{count}.csv'
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = users[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(users)
        
        print(f"✅ Generated {count} users saved to {filename}")
        return filename, users
    
    def process_users_concurrent(self, users, max_workers=10):
        """Process users with concurrent execution for scale testing"""
        
        print(f"🚀 Processing {len(users)} users with {max_workers} concurrent workers...")
        
        start_time = datetime.now()
        results = {
            'successful': [],
            'failed': [],
            'processing_times': []
        }
        
        # Process in batches to respect AWS API limits
        batch_size = 50
        batches = [users[i:i + batch_size] for i in range(0, len(users), batch_size)]
        
        for batch_num, batch in enumerate(batches, 1):
            print(f"📦 Processing Batch {batch_num}/{len(batches)} ({len(batch)} users)")
            batch_start = datetime.now()
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit tasks for concurrent processing
                future_to_user = {
                    executor.submit(self._process_single_user_safe, user): user 
                    for user in batch
                }
                
                # Collect results
                for future in as_completed(future_to_user):
                    user = future_to_user[future]
                    try:
                        result = future.result()
                        if result['status'] == 'success':
                            results['successful'].append(result)
                        else:
                            results['failed'].append(result)
                    except Exception as e:
                        results['failed'].append({
                            'username': user['username'],
                            'error': str(e),
                            'status': 'failed'
                        })
            
            batch_time = (datetime.now() - batch_start).total_seconds()
            results['processing_times'].append(batch_time)
            
            print(f"   ✅ Batch completed in {batch_time:.2f}s")
            print(f"   📊 Success: {len([r for r in results['successful'] if r.get('batch') == batch_num])}")
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        # Calculate metrics
        success_count = len(results['successful'])
        failure_count = len(results['failed'])
        success_rate = (success_count / len(users)) * 100
        throughput = len(users) / total_time
        
        print(f"\n📊 Scale Test Results:")
        print(f"   👥 Total Users: {len(users)}")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Failed: {failure_count}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        print(f"   ⏱️ Total Time: {total_time:.2f}s")
        print(f"   🚀 Throughput: {throughput:.2f} users/second")
        print(f"   ⚡ Avg Time/User: {total_time/len(users):.3f}s")
        
        return results
    
    def _process_single_user_safe(self, user):
        """Safely process a single user with error handling"""
        
        try:
            username = f"{user['username']}-{self.environment}"
            
            # Check if user already exists
            try:
                self.iam.get_user(UserName=username)
                return {
                    'username': username,
                    'status': 'skipped',
                    'reason': 'User already exists'
                }
            except self.iam.exceptions.NoSuchEntityException:
                pass  # User doesn't exist, proceed with creation
            
            # Create user with tags
            self.iam.create_user(
                UserName=username,
                Tags=[
                    {'Key': 'Environment', 'Value': self.environment},
                    {'Key': 'Department', 'Value': user['department']},
                    {'Key': 'Role', 'Value': user['role']},
                    {'Key': 'TestUser', 'Value': 'true'},
                    {'Key': 'CreatedBy', 'Value': 'ScaleTest'},
                    {'Key': 'CreatedDate', 'Value': datetime.now().isoformat()}
                ]
            )
            
            # Attach basic policy based on role
            policy_arn = self._get_policy_for_role(user['role'])
            if policy_arn:
                try:
                    self.iam.attach_user_policy(
                        UserName=username,
                        PolicyArn=policy_arn
                    )
                except Exception as e:
                    print(f"   ⚠️ Policy attachment failed for {username}: {e}")
            
            return {
                'username': username,
                'original_username': user['username'],
                'role': user['role'],
                'department': user['department'],
                'status': 'success',
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'username': user.get('username', 'unknown'),
                'status': 'failed',
                'error': str(e)
            }
    
    def _get_policy_for_role(self, role):
        """Get appropriate policy ARN for role"""
        
        role_policies = {
            'developer': 'arn:aws:iam::aws:policy/PowerUserAccess',
            'data-analyst': 'arn:aws:iam::aws:policy/job-function/DataScientist',
            'data-scientist': 'arn:aws:iam::aws:policy/job-function/DataScientist',
            'security-analyst': 'arn:aws:iam::aws:policy/SecurityAudit',
            'security-engineer': 'arn:aws:iam::aws:policy/SecurityAudit'
        }
        
        return role_policies.get(role, 'arn:aws:iam::aws:policy/ReadOnlyAccess')
    
    def cleanup_test_users(self, prefix='testuser'):
        """Clean up test users after scale testing"""
        
        print(f"🧹 Cleaning up test users with prefix '{prefix}'...")
        
        try:
            response = self.iam.list_users()
            test_users = [
                user['UserName'] for user in response['Users'] 
                if prefix in user['UserName'] and self.environment in user['UserName']
            ]
            
            print(f"Found {len(test_users)} test users to clean up")
            
            for username in test_users:
                try:
                    # Detach policies
                    attached_policies = self.iam.list_attached_user_policies(UserName=username)
                    for policy in attached_policies['AttachedPolicies']:
                        self.iam.detach_user_policy(
                            UserName=username,
                            PolicyArn=policy['PolicyArn']
                        )
                    
                    # Delete user
                    self.iam.delete_user(UserName=username)
                    print(f"   ✅ Deleted {username}")
                    
                except Exception as e:
                    print(f"   ❌ Failed to delete {username}: {e}")
            
            print(f"🧹 Cleanup completed")
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")

def main():
    """Main function with argument parsing"""
    
    parser = argparse.ArgumentParser(description='Scalable Enterprise IAM Deployment')
    parser.add_argument('--users', type=int, default=10, help='Number of users to create (default: 10)')
    parser.add_argument('--environment', default='dev', help='Environment (default: dev)')
    parser.add_argument('--cleanup', action='store_true', help='Clean up test users')
    parser.add_argument('--workers', type=int, default=10, help='Concurrent workers (default: 10)')
    
    args = parser.parse_args()
    
    deployment = ScalableEnterpriseIAMDeployment(environment=args.environment)
    
    if args.cleanup:
        deployment.cleanup_test_users()
        return
    
    print(f"🚀 Starting Scale Test with {args.users} users")
    print("=" * 50)
    
    # Generate test users
    filename, users = deployment.generate_test_users(args.users)
    
    # Process users concurrently
    results = deployment.process_users_concurrent(users, max_workers=args.workers)
    
    # Save results
    report = {
        'test_id': f"SCALE-TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        'timestamp': datetime.now().isoformat(),
        'parameters': {
            'user_count': args.users,
            'environment': args.environment,
            'concurrent_workers': args.workers
        },
        'results': results,
        'summary': {
            'total_users': args.users,
            'successful': len(results['successful']),
            'failed': len(results['failed']),
            'success_rate': f"{(len(results['successful'])/args.users)*100:.1f}%"
        }
    }
    
    report_filename = f'scale_test_report_{args.users}_users.json'
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Scale test report saved: {report_filename}")
    print(f"🎉 Scale test completed!")
    print(f"\n💡 To cleanup test users: python3 {__file__} --cleanup")

if __name__ == "__main__":
    main()
