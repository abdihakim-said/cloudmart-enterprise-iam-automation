import boto3
import json
from typing import Dict, List

class BedrockPolicyGeneratorV45:
    """Enhanced IAM policy generation using Claude Sonnet 4.5"""
    
    def __init__(self, region='us-east-1'):
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        self.model_id = "anthropic.claude-sonnet-4-5-20250929-v1:0"  # Latest Sonnet 4.5
    
    def generate_enterprise_policy(self, description: str, role_type: str, department: str = "") -> Dict:
        """Generate enterprise IAM policy with enhanced AI"""
        
        prompt = f"""
        You are an expert AWS IAM policy architect. Generate a secure, production-ready IAM policy.

        Requirements:
        - Role: {role_type}
        - Department: {department}
        - Description: {description}

        Create an IAM policy that follows these enterprise security principles:
        1. Least privilege access
        2. Include appropriate conditions (IP, MFA, time-based)
        3. Use specific resource ARNs where possible
        4. Include deny statements for security
        5. Add region restrictions
        6. Consider compliance requirements (SOC2, ISO27001)

        Return ONLY a valid JSON IAM policy document. No explanations.
        """
        
        response = self.bedrock.invoke_model(
            modelId=self.model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 3000,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        policy_text = result['content'][0]['text']
        
        # Clean up the response to extract JSON
        if '```json' in policy_text:
            policy_text = policy_text.split('```json')[1].split('```')[0]
        elif '```' in policy_text:
            policy_text = policy_text.split('```')[1].split('```')[0]
        
        try:
            policy = json.loads(policy_text.strip())
        except json.JSONDecodeError:
            # Fallback policy if AI response is malformed
            policy = self._generate_fallback_policy(role_type)
        
        return {
            'policy': policy,
            'description': description,
            'role_type': role_type,
            'department': department,
            'generated_by': 'claude-sonnet-4.5',
            'model_id': self.model_id
        }
    
    def analyze_policy_security(self, policy: Dict) -> Dict:
        """Enhanced security analysis with Claude 4.5"""
        
        prompt = f"""
        Analyze this IAM policy for security risks and compliance issues:

        {json.dumps(policy, indent=2)}

        Provide analysis in this JSON format:
        {{
            "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
            "security_score": 85,
            "risks": [
                {{"type": "PRIVILEGE_ESCALATION", "severity": "HIGH", "description": "..."}}
            ],
            "recommendations": [
                "Add MFA conditions",
                "Restrict to specific resources"
            ],
            "compliance": {{
                "soc2_compliant": true,
                "iso27001_compliant": false,
                "issues": ["Missing audit logging requirements"]
            }}
        }}
        """
        
        response = self.bedrock.invoke_model(
            modelId=self.model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        analysis_text = result['content'][0]['text']
        
        try:
            if '```json' in analysis_text:
                analysis_text = analysis_text.split('```json')[1].split('```')[0]
            analysis = json.loads(analysis_text.strip())
        except:
            analysis = {
                "risk_level": "MEDIUM",
                "security_score": 70,
                "risks": [{"type": "ANALYSIS_ERROR", "severity": "LOW", "description": "Could not parse AI analysis"}],
                "recommendations": ["Manual review required"],
                "compliance": {"soc2_compliant": False, "iso27001_compliant": False}
            }
        
        return analysis
    
    def _generate_fallback_policy(self, role_type: str) -> Dict:
        """Fallback policy if AI generation fails"""
        
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["sts:GetCallerIdentity"],
                    "Resource": "*",
                    "Condition": {
                        "Bool": {"aws:MultiFactorAuthPresent": "true"}
                    }
                }
            ]
        }

# Test the enhanced integration
if __name__ == "__main__":
    generator = BedrockPolicyGeneratorV45()
    
    result = generator.generate_enterprise_policy(
        "Senior DevOps engineer needs comprehensive access for CI/CD pipeline management",
        "devops-engineer",
        "Platform Engineering"
    )
    
    print("🤖 Claude Sonnet 4.5 Policy Generated:")
    print(json.dumps(result['policy'], indent=2))
