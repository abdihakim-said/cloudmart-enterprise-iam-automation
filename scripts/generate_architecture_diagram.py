#!/usr/bin/env python3
"""
Generate CloudMart Enterprise IAM Architecture Diagram
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.general import User, GenericSDK
from diagrams.aws.security import IAM, IAMPermissions, IAMRole
from diagrams.aws.storage import S3
from diagrams.aws.management import Cloudtrail, Cloudwatch
from diagrams.aws.ml import Bedrock

def create_architecture_diagram():
    """Create the CloudMart Enterprise IAM Architecture diagram"""
    
    with Diagram("CloudMart Enterprise IAM Architecture", 
                 filename="generated-diagrams/cloudmart-iam-architecture", 
                 show=False, 
                 direction="LR"):
        
        # Input Layer
        with Cluster("Input Sources"):
            admin_user = User("Admin User")
            csv_data = GenericSDK("CSV Data")
            api_input = GenericSDK("API Input")
        
        # AI Processing Layer
        with Cluster("AI Processing"):
            bedrock_ai = Bedrock("Amazon Bedrock\n(Claude 3 Sonnet)")
            policy_gen = GenericSDK("Policy Generator")
        
        # Core Processing Layer
        with Cluster("Core Automation Engine"):
            validator = GenericSDK("Compliance\nValidator")
            provisioner = GenericSDK("User\nProvisioner")
            terraform = GenericSDK("Terraform\nEngine")
        
        # AWS Infrastructure Layer
        with Cluster("AWS Infrastructure"):
            iam_service = IAM("IAM Service")
            s3_buckets = S3("S3 Buckets\n(Audit Logs)")
            cloudtrail_logs = Cloudtrail("CloudTrail\n(Audit Trail)")
        
        # Security Controls Layer
        with Cluster("Security Controls"):
            mfa_enforcement = IAMPermissions("MFA\nEnforcement")
            permission_boundaries = IAMPermissions("Permission\nBoundaries")
            iam_roles = IAMRole("IAM Roles\n(4 Enterprise Roles)")
        
        # Monitoring & Compliance Layer
        with Cluster("Monitoring & Compliance"):
            cloudwatch_metrics = Cloudwatch("CloudWatch\n(Metrics)")
            audit_logger = GenericSDK("Audit Logger\n(SOC2/ISO27001)")
            compliance_reports = GenericSDK("Compliance\nReports")
        
        # Flow connections with labels
        admin_user >> Edge(label="CSV Upload") >> csv_data
        admin_user >> Edge(label="API Calls") >> api_input
        
        csv_data >> Edge(label="Validate") >> validator
        api_input >> Edge(label="Validate") >> validator
        
        validator >> Edge(label="Generate") >> policy_gen
        policy_gen >> Edge(label="AI Processing") >> bedrock_ai
        bedrock_ai >> Edge(label="Policies") >> provisioner
        
        provisioner >> Edge(label="Deploy") >> terraform
        terraform >> Edge(label="Create Resources") >> iam_service
        
        iam_service >> Edge(label="Users/Roles") >> [s3_buckets, cloudtrail_logs]
        iam_service >> Edge(label="Security") >> [mfa_enforcement, permission_boundaries, iam_roles]
        
        cloudtrail_logs >> Edge(label="Audit Data") >> audit_logger
        audit_logger >> Edge(label="Reports") >> compliance_reports
        cloudwatch_metrics >> Edge(label="Metrics") >> compliance_reports

if __name__ == "__main__":
    create_architecture_diagram()
    print("✅ Architecture diagram generated: generated-diagrams/cloudmart-iam-architecture.png")
