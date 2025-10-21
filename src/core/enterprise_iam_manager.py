import boto3
import pandas as pd
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import hashlib

@dataclass
class UserRequest:
    username: str
    department: str
    role: str
    manager_email: str
    start_date: str
    access_level: str
    business_justification: str

class EnterpriseIAMManager:
    """Enterprise-grade IAM automation with compliance, audit trails, and RBAC"""
    
    def __init__(self, region='us-east-1', environment='dev'):
        self.iam = boto3.client('iam', region_name=region)
        self.sts = boto3.client('sts', region_name=region)
        self.cloudtrail = boto3.client('cloudtrail', region_name=region)
        self.environment = environment
        self.account_id = self.sts.get_caller_identity()['Account']
        
        # Enterprise role mappings
        self.role_mappings = {
            'developer': {
                'policies': ['arn:aws:iam::aws:policy/PowerUserAccess'],
                'boundary': 'DeveloperBoundary',
                'max_session': 28800  # 8 hours
            },
            'data-analyst': {
                'policies': ['arn:aws:iam::aws:policy/job-function/DataScientist'],
                'boundary': 'DataAnalystBoundary',
                'max_session': 14400  # 4 hours
            },
            'security-auditor': {
                'policies': ['arn:aws:iam::aws:policy/SecurityAudit'],
                'boundary': 'AuditorBoundary',
                'max_session': 3600   # 1 hour
            },
            'readonly': {
                'policies': ['arn:aws:iam::aws:policy/ReadOnlyAccess'],
                'boundary': 'ReadOnlyBoundary',
                'max_session': 43200  # 12 hours
            }
        }
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup enterprise audit logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'iam_audit_{self.environment}_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('EnterpriseIAM')
    
    def process_user_requests(self, csv_path: str) -> Dict:
        """Process bulk user requests with enterprise controls"""
        df = pd.read_csv(csv_path)
        results = {
            'successful': [],
            'failed': [],
            'pending_approval': [],
            'compliance_violations': []
        }
        
        for _, row in df.iterrows():
            try:
                user_request = UserRequest(**row.to_dict())
                result = self._process_single_user(user_request)
                results[result['status']].append(result)
                
            except Exception as e:
                results['failed'].append({
                    'username': row.get('username', 'unknown'),
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        self._generate_compliance_report(results)
        return results
    
    def _process_single_user(self, request: UserRequest) -> Dict:
        """Process individual user with enterprise validation"""
        
        # 1. Compliance validation
        compliance_check = self._validate_compliance(request)
        if not compliance_check['valid']:
            return {
                'status': 'compliance_violations',
                'username': request.username,
                'violations': compliance_check['violations'],
                'timestamp': datetime.now().isoformat()
            }
        
        # 2. Manager approval simulation (in real world, this would integrate with ServiceNow/Jira)
        if request.access_level == 'high' and not self._check_manager_approval(request):
            return {
                'status': 'pending_approval',
                'username': request.username,
                'manager': request.manager_email,
                'timestamp': datetime.now().isoformat()
            }
        
        # 3. Create user with enterprise controls
        try:
            user_arn = self._create_enterprise_user(request)
            
            # 4. Audit logging
            self._log_user_creation(request, user_arn)
            
            return {
                'status': 'successful',
                'username': request.username,
                'user_arn': user_arn,
                'role': request.role,
                'environment': self.environment,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create user {request.username}: {e}")
            return {
                'status': 'failed',
                'username': request.username,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _validate_compliance(self, request: UserRequest) -> Dict:
        """Enterprise compliance validation (SOC2, ISO27001)"""
        violations = []
        
        # Check role exists in approved list
        if request.role not in self.role_mappings:
            violations.append(f"Unauthorized role: {request.role}")
        
        # Check business justification
        if len(request.business_justification) < 20:
            violations.append("Insufficient business justification")
        
        # Check department authorization
        authorized_depts = ['engineering', 'data', 'security', 'finance']
        if request.department.lower() not in authorized_depts:
            violations.append(f"Unauthorized department: {request.department}")
        
        return {
            'valid': len(violations) == 0,
            'violations': violations
        }
    
    def _check_manager_approval(self, request: UserRequest) -> bool:
        """Simulate manager approval check (integrate with HR systems)"""
        # In real world: check ServiceNow, Workday, or custom approval system
        return True  # Simplified for demo
    
    def _create_enterprise_user(self, request: UserRequest) -> str:
        """Create user with enterprise security controls"""
        username = f"{request.username}-{self.environment}"
        role_config = self.role_mappings[request.role]
        
        # 1. Create IAM user
        self.iam.create_user(
            UserName=username,
            Tags=[
                {'Key': 'Environment', 'Value': self.environment},
                {'Key': 'Department', 'Value': request.department},
                {'Key': 'Manager', 'Value': request.manager_email},
                {'Key': 'CreatedBy', 'Value': 'IAMAutomation'},
                {'Key': 'AccessLevel', 'Value': request.access_level},
                {'Key': 'ComplianceId', 'Value': self._generate_compliance_id(request)}
            ]
        )
        
        # 2. Create and attach role
        role_name = f"{request.role}-{username}"
        assume_role_policy = self._generate_assume_role_policy(request)
        
        role_response = self.iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=assume_role_policy,
            MaxSessionDuration=role_config['max_session'],
            PermissionsBoundary=f"arn:aws:iam::{self.account_id}:policy/{role_config['boundary']}"
        )
        
        # 3. Attach managed policies
        for policy_arn in role_config['policies']:
            self.iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
        
        # 4. Enable MFA requirement
        self._enforce_mfa_policy(username)
        
        return role_response['Role']['Arn']
    
    def _generate_assume_role_policy(self, request: UserRequest) -> str:
        """Generate assume role policy with MFA and time restrictions"""
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::{self.account_id}:root"},
                    "Action": "sts:AssumeRole",
                    "Condition": {
                        "Bool": {"aws:MultiFactorAuthPresent": "true"},
                        "DateGreaterThan": {"aws:CurrentTime": request.start_date},
                        "IpAddress": {"aws:SourceIp": ["10.0.0.0/8", "172.16.0.0/12"]}  # Corporate IP ranges
                    }
                }
            ]
        }
        return json.dumps(policy)
    
    def _enforce_mfa_policy(self, username: str):
        """Enforce MFA requirement"""
        mfa_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Deny",
                    "Action": "*",
                    "Resource": "*",
                    "Condition": {
                        "BoolIfExists": {"aws:MultiFactorAuthPresent": "false"}
                    }
                }
            ]
        }
        
        self.iam.put_user_policy(
            UserName=username,
            PolicyName="EnforceMFA",
            PolicyDocument=json.dumps(mfa_policy)
        )
    
    def _generate_compliance_id(self, request: UserRequest) -> str:
        """Generate unique compliance tracking ID"""
        data = f"{request.username}{request.department}{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:12].upper()
    
    def _log_user_creation(self, request: UserRequest, user_arn: str):
        """Enterprise audit logging"""
        audit_event = {
            'event_type': 'USER_CREATED',
            'username': request.username,
            'user_arn': user_arn,
            'department': request.department,
            'role': request.role,
            'manager': request.manager_email,
            'environment': self.environment,
            'compliance_id': self._generate_compliance_id(request),
            'timestamp': datetime.now().isoformat(),
            'created_by': 'IAMAutomationSystem'
        }
        
        self.logger.info(f"AUDIT: {json.dumps(audit_event)}")
    
    def _generate_compliance_report(self, results: Dict):
        """Generate SOC2/ISO27001 compliance report"""
        report = {
            'report_id': f"IAM-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'environment': self.environment,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_requests': sum(len(v) for v in results.values()),
                'successful': len(results['successful']),
                'failed': len(results['failed']),
                'pending_approval': len(results['pending_approval']),
                'compliance_violations': len(results['compliance_violations'])
            },
            'compliance_status': 'COMPLIANT' if len(results['compliance_violations']) == 0 else 'NON_COMPLIANT',
            'details': results
        }
        
        # Save compliance report
        with open(f'compliance_report_{self.environment}_{datetime.now().strftime("%Y%m%d")}.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Compliance report generated: {report['report_id']}")

# Enterprise usage example
if __name__ == "__main__":
    manager = EnterpriseIAMManager(environment='dev')
    results = manager.process_user_requests('enterprise_users.csv')
    print(f"Processed {sum(len(v) for v in results.values())} user requests")
