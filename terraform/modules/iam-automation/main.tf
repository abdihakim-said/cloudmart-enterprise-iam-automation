# IAM Automation Module - Extends CloudMart Security Patterns
# Builds on existing EKS IAM, Security Groups, and KMS patterns

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Data sources to integrate with existing CloudMart infrastructure
data "aws_eks_cluster" "cloudmart" {
  name = "cloudmart-cluster"
}

data "aws_iam_openid_connect_provider" "cloudmart_oidc" {
  url = data.aws_eks_cluster.cloudmart.identity[0].oidc[0].issuer
}

data "aws_caller_identity" "current" {}

# Local values extending CloudMart patterns
locals {
  environments = ["dev", "qa", "staging", "prod"]
  
  # Role definitions following CloudMart naming conventions
  role_definitions = {
    developer = {
      description = "Developer access with CloudMart integration"
      max_session_duration = 3600
      mfa_age_limit = 3600
    }
    dba = {
      description = "Database administrator for CloudMart DynamoDB"
      max_session_duration = 7200
      mfa_age_limit = 1800
    }
    sre = {
      description = "SRE with CloudMart EKS and infrastructure access"
      max_session_duration = 14400
      mfa_age_limit = 900
    }
    security_auditor = {
      description = "Security auditor for CloudMart compliance"
      max_session_duration = 3600
      mfa_age_limit = 3600
    }
  }

  # Extend CloudMart tagging patterns
  common_tags = merge(var.tags, {
    Project     = "CloudMart-IAM"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Module      = "iam-automation"
    Integration = "cloudmart-extension"
  })
}

# Policy Boundary - Extends CloudMart security patterns
resource "aws_iam_policy" "cloudmart_policy_boundary" {
  name        = "CloudMart-PolicyBoundary-${var.environment}"
  description = "Policy boundary for CloudMart ${var.environment} environment"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DenyHighRiskActions"
        Effect = "Deny"
        Action = [
          "iam:CreateUser",
          "iam:DeleteUser",
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:AttachUserPolicy",
          "iam:DetachUserPolicy",
          "organizations:*",
          "account:*"
        ]
        Resource = "*"
        Condition = {
          StringNotEquals = {
            "aws:PrincipalTag/Environment" = var.environment
          }
        }
      },
      {
        Sid    = "RestrictToCloudMartResources"
        Effect = "Deny"
        Action = "*"
        Resource = "*"
        Condition = {
          StringNotLike = {
            "aws:RequestedRegion" = var.allowed_regions
          }
          ForAllValues:StringNotLike = {
            "aws:PrincipalArn" = [
              "arn:aws:iam::*:role/CloudMart*",
              "arn:aws:iam::*:role/aws-service-role/*"
            ]
          }
        }
      },
      {
        Sid    = "AllowCloudMartResourcesOnly"
        Effect = "Allow"
        Action = "*"
        Resource = [
          "arn:aws:dynamodb:*:*:table/cloudmart-*",
          "arn:aws:eks:*:*:cluster/cloudmart-*",
          "arn:aws:s3:::cloudmart-*",
          "arn:aws:lambda:*:*:function:cloudmart-*",
          "arn:aws:secretsmanager:*:*:secret:cloudmart/*"
        ]
      }
    ]
  })

  tags = local.common_tags
}

# Developer Role - Extends CloudMart EKS patterns
resource "aws_iam_role" "cloudmart_developer" {
  name                 = "CloudMart-Developer-${var.environment}"
  description          = local.role_definitions.developer.description
  max_session_duration = local.role_definitions.developer.max_session_duration
  permissions_boundary = aws_iam_policy.cloudmart_policy_boundary.arn

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          AWS = var.trusted_principals
        }
        Condition = {
          StringEquals = {
            "sts:ExternalId" = var.external_id
          }
          Bool = {
            "aws:MultiFactorAuthPresent" = "true"
          }
          NumericLessThan = {
            "aws:MultiFactorAuthAge" = local.role_definitions.developer.mfa_age_limit
          }
        }
      },
      # OIDC integration with existing CloudMart EKS cluster
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = data.aws_iam_openid_connect_provider.cloudmart_oidc.arn
        }
        Condition = {
          StringEquals = {
            "${replace(data.aws_iam_openid_connect_provider.cloudmart_oidc.url, "https://", "")}:sub" = "system:serviceaccount:${var.environment}:cloudmart-developer-sa"
            "${replace(data.aws_iam_openid_connect_provider.cloudmart_oidc.url, "https://", "")}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "CloudMart-Developer-${var.environment}"
    Role = "developer"
  })
}

# Developer Policy - CloudMart resource access
resource "aws_iam_policy" "cloudmart_developer_policy" {
  name        = "CloudMart-Developer-Policy-${var.environment}"
  description = "Developer permissions for CloudMart ${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudMartDynamoDBReadOnly"
        Effect = "Allow"
        Action = [
          "dynamodb:DescribeTable",
          "dynamodb:Query",
          "dynamodb:GetItem",
          "dynamodb:BatchGetItem",
          "dynamodb:Scan"
        ]
        Resource = [
          "arn:aws:dynamodb:*:*:table/cloudmart-products",
          "arn:aws:dynamodb:*:*:table/cloudmart-orders",
          "arn:aws:dynamodb:*:*:table/cloudmart-tickets",
          "arn:aws:dynamodb:*:*:table/cloudmart-*-${var.environment}"
        ]
      },
      {
        Sid    = "CloudMartEKSReadOnly"
        Effect = "Allow"
        Action = [
          "eks:DescribeCluster",
          "eks:DescribeNodegroup",
          "eks:ListClusters",
          "eks:ListNodegroups"
        ]
        Resource = "arn:aws:eks:*:*:cluster/cloudmart-*"
      },
      {
        Sid    = "CloudMartLogsAccess"
        Effect = "Allow"
        Action = [
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:GetLogEvents",
          "logs:FilterLogEvents"
        ]
        Resource = [
          "arn:aws:logs:*:*:log-group:/aws/eks/cloudmart-*",
          "arn:aws:logs:*:*:log-group:/aws/lambda/cloudmart-*"
        ]
      },
      {
        Sid    = "CloudMartSecretsReadOnly"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = "arn:aws:secretsmanager:*:*:secret:cloudmart/${var.environment}/*"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "cloudmart_developer_policy" {
  role       = aws_iam_role.cloudmart_developer.name
  policy_arn = aws_iam_policy.cloudmart_developer_policy.arn
}

# SRE Role - Extends CloudMart EKS admin patterns
resource "aws_iam_role" "cloudmart_sre" {
  name                 = "CloudMart-SRE-${var.environment}"
  description          = local.role_definitions.sre.description
  max_session_duration = local.role_definitions.sre.max_session_duration
  permissions_boundary = aws_iam_policy.cloudmart_policy_boundary.arn

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          AWS = var.trusted_principals
        }
        Condition = {
          StringEquals = {
            "sts:ExternalId" = var.external_id
          }
          Bool = {
            "aws:MultiFactorAuthPresent" = "true"
          }
          NumericLessThan = {
            "aws:MultiFactorAuthAge" = local.role_definitions.sre.mfa_age_limit
          }
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "CloudMart-SRE-${var.environment}"
    Role = "sre"
  })
}

# SRE Policy - CloudMart infrastructure management
resource "aws_iam_policy" "cloudmart_sre_policy" {
  name        = "CloudMart-SRE-Policy-${var.environment}"
  description = "SRE permissions for CloudMart ${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudMartEKSAdmin"
        Effect = "Allow"
        Action = [
          "eks:*"
        ]
        Resource = "arn:aws:eks:*:*:cluster/cloudmart-*"
      },
      {
        Sid    = "CloudMartDynamoDBAdmin"
        Effect = "Allow"
        Action = [
          "dynamodb:*"
        ]
        Resource = [
          "arn:aws:dynamodb:*:*:table/cloudmart-*",
          "arn:aws:dynamodb:*:*:table/cloudmart-*/index/*",
          "arn:aws:dynamodb:*:*:table/cloudmart-*/stream/*"
        ]
      },
      {
        Sid    = "CloudMartMonitoring"
        Effect = "Allow"
        Action = [
          "cloudwatch:*",
          "logs:*"
        ]
        Resource = "*"
        Condition = {
          StringLike = {
            "aws:RequestTag/Project" = "CloudMart*"
          }
        }
      },
      {
        Sid    = "CloudMartLambdaAdmin"
        Effect = "Allow"
        Action = [
          "lambda:*"
        ]
        Resource = "arn:aws:lambda:*:*:function:cloudmart-*"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "cloudmart_sre_policy" {
  role       = aws_iam_role.cloudmart_sre.name
  policy_arn = aws_iam_policy.cloudmart_sre_policy.arn
}

# CloudWatch Log Group for IAM events - Extends CloudMart logging patterns
resource "aws_cloudwatch_log_group" "cloudmart_iam_events" {
  name              = "/aws/iam/cloudmart-${var.environment}"
  retention_in_days = var.log_retention_days
  
  # Use existing CloudMart KMS key if available, otherwise create new
  kms_key_id = var.kms_key_arn != "" ? var.kms_key_arn : aws_kms_key.iam_encryption[0].arn

  tags = merge(local.common_tags, {
    Name = "cloudmart-iam-${var.environment}-logs"
  })
}

# KMS Key for IAM encryption (only if not provided)
resource "aws_kms_key" "iam_encryption" {
  count = var.kms_key_arn == "" ? 1 : 0
  
  description             = "IAM encryption key for CloudMart ${var.environment}"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "cloudmart-iam-${var.environment}-kms"
  })
}

resource "aws_kms_alias" "iam_encryption" {
  count = var.kms_key_arn == "" ? 1 : 0
  
  name          = "alias/cloudmart-iam-${var.environment}"
  target_key_id = aws_kms_key.iam_encryption[0].key_id
}

# CloudTrail for IAM audit logging - Extends CloudMart compliance patterns
resource "aws_cloudtrail" "cloudmart_iam_audit" {
  count = var.enable_audit_logging ? 1 : 0
  
  name           = "cloudmart-iam-audit-${var.environment}"
  s3_bucket_name = aws_s3_bucket.cloudmart_audit_logs[0].bucket

  event_selector {
    read_write_type                 = "All"
    include_management_events       = true
    exclude_management_event_sources = []

    data_resource {
      type   = "AWS::IAM::Role"
      values = ["arn:aws:iam::*:role/CloudMart*"]
    }
  }

  tags = merge(local.common_tags, {
    Name = "cloudmart-iam-audit-${var.environment}"
  })
}

# S3 bucket for audit logs
resource "aws_s3_bucket" "cloudmart_audit_logs" {
  count = var.enable_audit_logging ? 1 : 0
  
  bucket        = "cloudmart-iam-audit-logs-${var.environment}-${random_id.bucket_suffix[0].hex}"
  force_destroy = var.environment != "prod"

  tags = merge(local.common_tags, {
    Name = "cloudmart-iam-audit-logs-${var.environment}"
  })
}

resource "random_id" "bucket_suffix" {
  count = var.enable_audit_logging ? 1 : 0
  byte_length = 4
}

# S3 bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "cloudmart_audit_logs" {
  count = var.enable_audit_logging ? 1 : 0
  
  bucket = aws_s3_bucket.cloudmart_audit_logs[0].id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_arn != "" ? var.kms_key_arn : aws_kms_key.iam_encryption[0].arn
      sse_algorithm     = "aws:kms"
    }
  }
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "cloudmart_audit_logs" {
  count = var.enable_audit_logging ? 1 : 0
  
  bucket = aws_s3_bucket.cloudmart_audit_logs[0].id
  versioning_configuration {
    status = "Enabled"
  }
}
