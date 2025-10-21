variable "environment" {
  description = "Environment name"
  type        = string
}

variable "company_name" {
  description = "Company name for resource naming"
  type        = string
  default     = "cloudmart"
}

# Permission Boundaries for Enterprise Security
resource "aws_iam_policy" "developer_boundary" {
  name        = "DeveloperBoundary-${var.environment}"
  description = "Permission boundary for developers"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:*",
          "s3:*",
          "lambda:*",
          "apigateway:*",
          "cloudformation:*",
          "logs:*",
          "cloudwatch:*"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:RequestedRegion" = ["us-east-1", "us-west-2"]
          }
        }
      },
      {
        Effect = "Deny"
        Action = [
          "iam:*",
          "organizations:*",
          "account:*"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "data_analyst_boundary" {
  name        = "DataAnalystBoundary-${var.environment}"
  description = "Permission boundary for data analysts"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject*",
          "s3:ListBucket",
          "athena:*",
          "glue:*",
          "redshift:Describe*",
          "redshift:List*",
          "quicksight:*"
        ]
        Resource = "*"
      },
      {
        Effect = "Deny"
        Action = [
          "s3:DeleteObject*",
          "s3:PutObject*"
        ]
        Resource = "*"
        Condition = {
          StringNotEquals = {
            "s3:prefix" = ["analytics/", "reports/"]
          }
        }
      }
    ]
  })
}

# Service Control Policy for Organization-level governance
resource "aws_organizations_policy" "enterprise_scp" {
  count = var.environment == "prod" ? 1 : 0
  
  name        = "${var.company_name}-enterprise-scp"
  description = "Enterprise Service Control Policy"
  type        = "SERVICE_CONTROL_POLICY"
  
  content = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Deny"
        Action = [
          "ec2:TerminateInstances",
          "rds:DeleteDBInstance",
          "s3:DeleteBucket"
        ]
        Resource = "*"
        Condition = {
          StringNotEquals = {
            "aws:PrincipalTag/Department" = ["engineering", "devops"]
          }
        }
      },
      {
        Effect = "Deny"
        Action = "*"
        Resource = "*"
        Condition = {
          StringNotEquals = {
            "aws:RequestedRegion" = ["us-east-1", "us-west-2", "eu-west-1"]
          }
        }
      }
    ]
  })
}

# CloudTrail for audit logging
resource "aws_cloudtrail" "enterprise_audit" {
  name           = "${var.company_name}-audit-trail-${var.environment}"
  s3_bucket_name = aws_s3_bucket.audit_logs.bucket
  
  event_selector {
    read_write_type                 = "All"
    include_management_events       = true
    exclude_management_event_sources = []
    
    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:aws:s3:::*/*"]
    }
  }
  
  insight_selector {
    insight_type = "ApiCallRateInsight"
  }
}

resource "aws_s3_bucket" "audit_logs" {
  bucket        = "${var.company_name}-audit-logs-${var.environment}-${random_id.bucket_suffix.hex}"
  force_destroy = var.environment != "prod"
}

resource "aws_s3_bucket_versioning" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id
  
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# IAM Access Analyzer for continuous compliance
resource "aws_accessanalyzer_analyzer" "enterprise_analyzer" {
  analyzer_name = "${var.company_name}-access-analyzer-${var.environment}"
  type          = "ACCOUNT"
  
  tags = {
    Environment = var.environment
    Purpose     = "Enterprise IAM Compliance"
  }
}

# Config Rules for compliance monitoring
resource "aws_config_configuration_recorder" "enterprise_recorder" {
  name     = "${var.company_name}-config-recorder-${var.environment}"
  role_arn = aws_iam_role.config_role.arn
  
  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}

resource "aws_iam_role" "config_role" {
  name = "${var.company_name}-config-role-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "config_role_policy" {
  role       = aws_iam_role.config_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/ConfigRole"
}

# Output enterprise resources
output "permission_boundaries" {
  value = {
    developer_boundary    = aws_iam_policy.developer_boundary.arn
    data_analyst_boundary = aws_iam_policy.data_analyst_boundary.arn
  }
}

output "audit_resources" {
  value = {
    cloudtrail_arn    = aws_cloudtrail.enterprise_audit.arn
    audit_bucket      = aws_s3_bucket.audit_logs.bucket
    access_analyzer   = aws_accessanalyzer_analyzer.enterprise_analyzer.arn
  }
}
