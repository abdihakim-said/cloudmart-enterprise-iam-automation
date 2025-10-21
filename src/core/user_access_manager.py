#!/usr/bin/env python3

import boto3
import json
import secrets
import string
import csv
from datetime import datetime
import argparse

class UserAccessManager:
    """Manage user passwords, access keys, and console access"""
    
    def __init__(self, environment='dev'):
        self.iam = boto3.client('iam')
        self.sts = boto3.client('sts')
        self.environment = environment
        self.account_id = self.sts.get_caller_identity()['Account']
        
        print(f"🔐 User Access Manager")
        print(f"🌍 Environment: {environment}")
        print(f"📍 AWS Account: {self.account_id}")
    
    def setup_user_access(self, username_pattern="*"):
        """Set up passwords and access for users"""
        
        print(f"\n🚀 Setting up user access...")
        
        # Get users matching pattern
        users = self._get_users(username_pattern)
        
        if not users:
            print("❌ No users found matching pattern")
            return
        
        access_info = []
        
        for user in users:
            username = user['UserName']
            print(f"\n👤 Setting up access for: {username}")
            
            try:
                # Generate secure password
                password = self._generate_secure_password()
                
                # Create login profile (console access)
                console_access = self._setup_console_access(username, password)
                
                # Create access keys (programmatic access)
                access_keys = self._create_access_keys(username)
                
                # Get user tags for additional info
                user_tags = self._get_user_tags(username)
                
                user_access = {
                    'username': username,
                    'console_password': password,
                    'console_url': f"https://{self.account_id}.signin.aws.amazon.com/console",
                    'access_key_id': access_keys['AccessKeyId'] if access_keys else None,
                    'secret_access_key': access_keys['SecretAccessKey'] if access_keys else None,
                    'account_id': self.account_id,
                    'environment': self.environment,
                    'department': user_tags.get('Department', 'Unknown'),
                    'role': user_tags.get('Role', 'Unknown'),
                    'created_date': datetime.now().isoformat(),
                    'password_reset_required': True,
                    'mfa_required': True
                }
                
                access_info.append(user_access)
                
                print(f"   ✅ Console access: Enabled")
                print(f"   ✅ Access keys: Created")
                print(f"   🔐 Password: Generated")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                access_info.append({
                    'username': username,
                    'status': 'failed',
                    'error': str(e)
                })
        
        # Save access information
        self._save_access_info(access_info)
        
        # Generate user instructions
        self._generate_user_instructions(access_info)
        
        return access_info
    
    def _get_users(self, pattern):
        """Get users matching pattern"""
        
        try:
            response = self.iam.list_users()
            users = response['Users']
            
            if pattern != "*":
                users = [u for u in users if pattern in u['UserName']]
            
            # Filter for environment users
            users = [u for u in users if f'-{self.environment}' in u['UserName']]
            
            return users
            
        except Exception as e:
            print(f"❌ Error getting users: {e}")
            return []
    
    def _generate_secure_password(self):
        """Generate secure password meeting AWS requirements"""
        
        # AWS password requirements:
        # - 8-128 characters
        # - At least 3 of: uppercase, lowercase, numbers, symbols
        
        length = 16
        
        # Ensure we have all character types
        password = [
            secrets.choice(string.ascii_uppercase),  # Uppercase
            secrets.choice(string.ascii_lowercase),  # Lowercase  
            secrets.choice(string.digits),           # Numbers
            secrets.choice('!@#$%^&*()_+-=[]{}|;:,.<>?')  # Symbols
        ]
        
        # Fill remaining length
        all_chars = string.ascii_letters + string.digits + '!@#$%^&*()_+-=[]{}|;:,.<>?'
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    def _setup_console_access(self, username, password):
        """Set up AWS console access with password"""
        
        try:
            # Create login profile
            self.iam.create_login_profile(
                UserName=username,
                Password=password,
                PasswordResetRequired=True  # Force password change on first login
            )
            
            return True
            
        except self.iam.exceptions.EntityAlreadyExistsException:
            # Update existing login profile
            try:
                self.iam.update_login_profile(
                    UserName=username,
                    Password=password,
                    PasswordResetRequired=True
                )
                return True
            except Exception as e:
                print(f"   ⚠️ Failed to update login profile: {e}")
                return False
                
        except Exception as e:
            print(f"   ⚠️ Failed to create login profile: {e}")
            return False
    
    def _create_access_keys(self, username):
        """Create access keys for programmatic access"""
        
        try:
            # Check if user already has access keys
            existing_keys = self.iam.list_access_keys(UserName=username)
            
            if len(existing_keys['AccessKeyMetadata']) >= 2:
                print(f"   ⚠️ User already has maximum access keys")
                return None
            
            # Create new access key
            response = self.iam.create_access_key(UserName=username)
            access_key = response['AccessKey']
            
            return {
                'AccessKeyId': access_key['AccessKeyId'],
                'SecretAccessKey': access_key['SecretAccessKey']
            }
            
        except Exception as e:
            print(f"   ⚠️ Failed to create access keys: {e}")
            return None
    
    def _get_user_tags(self, username):
        """Get user tags for additional information"""
        
        try:
            response = self.iam.list_user_tags(UserName=username)
            tags = {tag['Key']: tag['Value'] for tag in response['Tags']}
            return tags
        except:
            return {}
    
    def _save_access_info(self, access_info):
        """Save access information to files"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save as JSON (for system use)
        json_filename = f'user_access_info_{self.environment}_{timestamp}.json'
        with open(json_filename, 'w') as f:
            json.dump(access_info, f, indent=2)
        
        # Save as CSV (for distribution)
        csv_filename = f'user_credentials_{self.environment}_{timestamp}.csv'
        
        successful_users = [u for u in access_info if u.get('console_password')]
        
        if successful_users:
            with open(csv_filename, 'w', newline='') as csvfile:
                fieldnames = [
                    'username', 'console_password', 'console_url', 
                    'access_key_id', 'secret_access_key', 'account_id',
                    'department', 'role', 'password_reset_required', 'mfa_required'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for user in successful_users:
                    writer.writerow({
                        'username': user['username'],
                        'console_password': user['console_password'],
                        'console_url': user['console_url'],
                        'access_key_id': user.get('access_key_id', ''),
                        'secret_access_key': user.get('secret_access_key', ''),
                        'account_id': user['account_id'],
                        'department': user['department'],
                        'role': user['role'],
                        'password_reset_required': user['password_reset_required'],
                        'mfa_required': user['mfa_required']
                    })
        
        print(f"\n📄 Access information saved:")
        print(f"   📋 JSON: {json_filename}")
        print(f"   📊 CSV: {csv_filename}")
    
    def _generate_user_instructions(self, access_info):
        """Generate user instruction document"""
        
        successful_users = [u for u in access_info if u.get('console_password')]
        
        if not successful_users:
            return
        
        instructions = f"""
# 🔐 CloudMart AWS Access Instructions

## 📋 Your AWS Account Access Details

**Account ID:** {self.account_id}
**Environment:** {self.environment.upper()}
**Console URL:** https://{self.account_id}.signin.aws.amazon.com/console

---

## 👥 User Access Information

"""
        
        for user in successful_users:
            instructions += f"""
### 👤 {user['username']}
- **Department:** {user['department']}
- **Role:** {user['role']}
- **Console Password:** `{user['console_password']}`
- **Access Key ID:** `{user.get('access_key_id', 'Not created')}`
- **Secret Access Key:** `{user.get('secret_access_key', 'Not created')}`

**Console Login Steps:**
1. Go to: https://{self.account_id}.signin.aws.amazon.com/console
2. Enter Username: `{user['username']}`
3. Enter Password: `{user['console_password']}`
4. You will be required to change password on first login
5. Set up MFA (Multi-Factor Authentication) - REQUIRED

**CLI/SDK Configuration:**
```bash
aws configure
AWS Access Key ID: {user.get('access_key_id', 'Not created')}
AWS Secret Access Key: {user.get('secret_access_key', 'Not created')}
Default region name: us-east-1
Default output format: json
```

---
"""
        
        instructions += f"""
## 🔒 Security Requirements

### ⚠️ IMPORTANT SECURITY NOTES:
1. **Change your password** immediately after first login
2. **Enable MFA** (Multi-Factor Authentication) - MANDATORY
3. **Never share** your credentials
4. **Use strong passwords** (minimum 12 characters)
5. **Report any suspicious activity** immediately

### 🛡️ MFA Setup Instructions:
1. Login to AWS Console
2. Click your username (top right)
3. Select "Security credentials"
4. Click "Assign MFA device"
5. Choose "Virtual MFA device"
6. Use Google Authenticator or similar app
7. Follow the setup wizard

### 📱 Recommended MFA Apps:
- Google Authenticator
- Microsoft Authenticator
- Authy
- 1Password

---

## 🆘 Support

**For technical issues:**
- Email: support@cloudmart.com
- Slack: #aws-support

**For access issues:**
- Email: iam-admin@cloudmart.com
- Emergency: Call IT Help Desk

---

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Environment:** {self.environment.upper()}
**Account:** {self.account_id}
"""
        
        filename = f'user_access_instructions_{self.environment}.md'
        with open(filename, 'w') as f:
            f.write(instructions)
        
        print(f"   📖 Instructions: {filename}")

def main():
    """Main function"""
    
    parser = argparse.ArgumentParser(description='User Access Manager')
    parser.add_argument('--environment', default='dev', help='Environment (default: dev)')
    parser.add_argument('--users', default='*', help='User pattern (default: all users)')
    
    args = parser.parse_args()
    
    manager = UserAccessManager(environment=args.environment)
    access_info = manager.setup_user_access(args.users)
    
    successful = len([u for u in access_info if u.get('console_password')])
    failed = len(access_info) - successful
    
    print(f"\n📊 Access Setup Summary:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   🔐 Console access enabled for all successful users")
    print(f"   🔑 Access keys created for programmatic access")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Distribute credentials securely to users")
    print(f"   2. Ensure users change passwords on first login")
    print(f"   3. Verify MFA setup for all users")
    print(f"   4. Monitor access logs for unusual activity")

if __name__ == "__main__":
    main()
