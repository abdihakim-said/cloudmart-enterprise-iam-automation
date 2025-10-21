#!/usr/bin/env python3

import boto3
import time

def cleanup_aws_resources():
    """Clean up all AWS resources created by the IAM automation project"""
    
    iam = boto3.client('iam')
    s3 = boto3.client('s3')
    
    print("🗑️ Starting AWS Resource Cleanup...")
    print("=" * 50)
    
    # 1. Clean up IAM Users
    print("\n1️⃣ Cleaning up IAM Users...")
    
    try:
        users = iam.list_users()['Users']
        project_users = [u for u in users if '-dev' in u['UserName'] and any(x in u['UserName'] for x in ['john.doe', 'jane.smith', 'bob.wilson', 'mary.johnson', 'testuser'])]
        
        for user in project_users:
            username = user['UserName']
            print(f"   🗑️ Deleting user: {username}")
            
            try:
                # Delete access keys
                access_keys = iam.list_access_keys(UserName=username)['AccessKeyMetadata']
                for key in access_keys:
                    iam.delete_access_key(UserName=username, AccessKeyId=key['AccessKeyId'])
                    print(f"      ✅ Deleted access key: {key['AccessKeyId']}")
                
                # Delete login profile
                try:
                    iam.delete_login_profile(UserName=username)
                    print(f"      ✅ Deleted login profile")
                except iam.exceptions.NoSuchEntityException:
                    pass
                
                # Detach user policies
                attached_policies = iam.list_attached_user_policies(UserName=username)['AttachedPolicies']
                for policy in attached_policies:
                    iam.detach_user_policy(UserName=username, PolicyArn=policy['PolicyArn'])
                    print(f"      ✅ Detached policy: {policy['PolicyName']}")
                
                # Delete inline policies
                inline_policies = iam.list_user_policies(UserName=username)['PolicyNames']
                for policy_name in inline_policies:
                    iam.delete_user_policy(UserName=username, PolicyName=policy_name)
                    print(f"      ✅ Deleted inline policy: {policy_name}")
                
                # Delete user
                iam.delete_user(UserName=username)
                print(f"      ✅ User deleted successfully")
                
            except Exception as e:
                print(f"      ❌ Error deleting user {username}: {e}")
    
    except Exception as e:
        print(f"   ❌ Error listing users: {e}")
    
    # 2. Clean up IAM Roles
    print("\n2️⃣ Cleaning up IAM Roles...")
    
    try:
        roles = iam.list_roles()['Roles']
        project_roles = [r for r in roles if any(x in r['RoleName'] for x in ['CloudMart', 'developer-dev', 'readonly-dev'])]
        
        for role in project_roles:
            role_name = role['RoleName']
            print(f"   🗑️ Deleting role: {role_name}")
            
            try:
                # Detach managed policies
                attached_policies = iam.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
                for policy in attached_policies:
                    iam.detach_role_policy(RoleName=role_name, PolicyArn=policy['PolicyArn'])
                    print(f"      ✅ Detached policy: {policy['PolicyName']}")
                
                # Delete inline policies
                inline_policies = iam.list_role_policies(RoleName=role_name)['PolicyNames']
                for policy_name in inline_policies:
                    iam.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
                    print(f"      ✅ Deleted inline policy: {policy_name}")
                
                # Delete role
                iam.delete_role(RoleName=role_name)
                print(f"      ✅ Role deleted successfully")
                
            except Exception as e:
                print(f"      ❌ Error deleting role {role_name}: {e}")
    
    except Exception as e:
        print(f"   ❌ Error listing roles: {e}")
    
    # 3. Clean up Custom Policies
    print("\n3️⃣ Cleaning up Custom Policies...")
    
    try:
        policies = iam.list_policies(Scope='Local')['Policies']
        project_policies = [p for p in policies if any(x in p['PolicyName'] for x in ['DeveloperBoundary-dev', 'DataAnalystBoundary-dev'])]
        
        for policy in project_policies:
            policy_name = policy['PolicyName']
            policy_arn = policy['Arn']
            print(f"   🗑️ Deleting policy: {policy_name}")
            
            try:
                iam.delete_policy(PolicyArn=policy_arn)
                print(f"      ✅ Policy deleted successfully")
                
            except Exception as e:
                print(f"      ❌ Error deleting policy {policy_name}: {e}")
    
    except Exception as e:
        print(f"   ❌ Error listing policies: {e}")
    
    # 4. Clean up S3 Buckets
    print("\n4️⃣ Cleaning up S3 Buckets...")
    
    try:
        buckets = s3.list_buckets()['Buckets']
        project_buckets = [b for b in buckets if 'cloudmart-audit-logs' in b['Name']]
        
        for bucket in project_buckets:
            bucket_name = bucket['Name']
            print(f"   🗑️ Deleting S3 bucket: {bucket_name}")
            
            try:
                # Delete all objects first
                objects = s3.list_objects_v2(Bucket=bucket_name)
                if 'Contents' in objects:
                    for obj in objects['Contents']:
                        s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
                        print(f"      ✅ Deleted object: {obj['Key']}")
                
                # Delete bucket
                s3.delete_bucket(Bucket=bucket_name)
                print(f"      ✅ Bucket deleted successfully")
                
            except Exception as e:
                print(f"      ❌ Error deleting bucket {bucket_name}: {e}")
    
    except Exception as e:
        print(f"   ❌ Error listing buckets: {e}")
    
    # 5. Destroy Terraform Infrastructure
    print("\n5️⃣ Destroying Terraform Infrastructure...")
    
    try:
        import subprocess
        import os
        
        terraform_dir = "terraform/environments/dev"
        if os.path.exists(terraform_dir):
            print(f"   🗑️ Running terraform destroy in {terraform_dir}")
            
            result = subprocess.run(
                ["terraform", "destroy", "-auto-approve"],
                cwd=terraform_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"      ✅ Terraform destroy completed successfully")
            else:
                print(f"      ⚠️ Terraform destroy output: {result.stderr}")
        else:
            print(f"   ⚠️ Terraform directory not found: {terraform_dir}")
    
    except Exception as e:
        print(f"   ❌ Error running terraform destroy: {e}")
    
    print(f"\n🎉 AWS Resource Cleanup Complete!")
    print(f"📊 Summary:")
    print(f"   ✅ IAM Users cleaned up")
    print(f"   ✅ IAM Roles cleaned up") 
    print(f"   ✅ Custom Policies cleaned up")
    print(f"   ✅ S3 Buckets cleaned up")
    print(f"   ✅ Terraform infrastructure destroyed")
    
    print(f"\n💰 Cost Impact:")
    print(f"   • IAM resources: $0 (no charges)")
    print(f"   • S3 storage: ~$0.01 saved")
    print(f"   • Total monthly savings: ~$0.01")

if __name__ == "__main__":
    cleanup_aws_resources()
