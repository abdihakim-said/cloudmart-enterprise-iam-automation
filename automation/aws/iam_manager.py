import boto3
import pandas as pd
import logging
from typing import Dict, List

class IAMManager:
    def __init__(self, region='us-east-1'):
        self.iam = boto3.client('iam', region_name=region)
        self.sts = boto3.client('sts', region_name=region)
        
    def create_user_from_csv(self, csv_path: str, environment: str):
        """Create users from CSV file"""
        df = pd.read_csv(csv_path)
        results = []
        
        for _, row in df.iterrows():
            try:
                username = f"{row['username']}-{environment}"
                self.iam.create_user(UserName=username)
                
                # Attach role if specified
                if 'role' in row and row['role']:
                    role_arn = f"arn:aws:iam::{self.get_account_id()}:role/{row['role']}-{environment}"
                    self.attach_user_policy(username, role_arn)
                
                results.append({'user': username, 'status': 'created'})
                logging.info(f"Created user: {username}")
                
            except Exception as e:
                results.append({'user': row['username'], 'status': f'error: {str(e)}'})
                logging.error(f"Failed to create user {row['username']}: {e}")
        
        return results
    
    def get_account_id(self):
        return self.sts.get_caller_identity()['Account']
    
    def attach_user_policy(self, username: str, policy_arn: str):
        """Attach policy to user"""
        self.iam.attach_user_policy(UserName=username, PolicyArn=policy_arn)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager = IAMManager()
    # Example usage: manager.create_user_from_csv('users.csv', 'dev')
