import boto3
import json
from typing import Dict, List

class BedrockPolicyGenerator:
    """AI-powered IAM policy generation using Amazon Bedrock"""
    
    def __init__(self, region='us-east-1'):
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    def generate_policy_from_description(self, description: str, role_type: str) -> Dict:
        """Generate IAM policy from natural language description"""
        
        prompt = f"""
        Generate an AWS IAM policy for a {role_type} role based on this description:
        "{description}"
        
        Requirements:
        - Follow least privilege principle
        - Include appropriate conditions
        - Use specific resource ARNs where possible
        - Include deny statements for security
        
        Return only valid JSON policy document.
        """
        
        response = self.bedrock.invoke_model(
            modelId=self.model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        policy_json = result['content'][0]['text']
        
        return {
            'policy': json.loads(policy_json),
            'description': description,
            'role_type': role_type,
            'generated_by': 'bedrock-ai'
        }
    
    def analyze_policy_risks(self, policy: Dict) -> List[str]:
        """AI-powered policy risk analysis"""
        
        prompt = f"""
        Analyze this IAM policy for security risks:
        {json.dumps(policy, indent=2)}
        
        Identify:
        - Overly permissive actions
        - Missing conditions
        - Potential privilege escalation
        - Resource wildcards
        
        Return list of specific risks found.
        """
        
        response = self.bedrock.invoke_model(
            modelId=self.model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text'].split('\n')

# Usage example
if __name__ == "__main__":
    generator = BedrockPolicyGenerator()
    policy = generator.generate_policy_from_description(
        "Data scientist needs access to S3 buckets for ML training data and SageMaker for model training",
        "data-scientist"
    )
