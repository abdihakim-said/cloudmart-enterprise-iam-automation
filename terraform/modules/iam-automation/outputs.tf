# IAM Automation Module Outputs
# Follows CloudMart output patterns

# Role ARNs
output "developer_role_arn" {
  description = "ARN of the CloudMart developer role"
  value       = aws_iam_role.cloudmart_developer.arn
}

output "developer_role_name" {
  description = "Name of the CloudMart developer role"
  value       = aws_iam_role.cloudmart_developer.name
}

output "sre_role_arn" {
  description = "ARN of the CloudMart SRE role"
  value       = aws_iam_role.cloudmart_sre.arn
}

output "sre_role_name" {
  description = "Name of the CloudMart SRE role"
  value       = aws_iam_role.cloudmart_sre.name
}

# Policy ARNs
output "policy_boundary_arn" {
  description = "ARN of the CloudMart policy boundary"
  value       = aws_iam_policy.cloudmart_policy_boundary.arn
}

output "developer_policy_arn" {
  description = "ARN of the CloudMart developer policy"
  value       = aws_iam_policy.cloudmart_developer_policy.arn
}

output "sre_policy_arn" {
  description = "ARN of the CloudMart SRE policy"
  value       = aws_iam_policy.cloudmart_sre_policy.arn
}

# KMS and Encryption
output "kms_key_id" {
  description = "ID of the IAM encryption KMS key"
  value       = var.kms_key_arn != "" ? var.kms_key_arn : (length(aws_kms_key.iam_encryption) > 0 ? aws_kms_key.iam_encryption[0].key_id : null)
}

output "kms_key_arn" {
  description = "ARN of the IAM encryption KMS key"
  value       = var.kms_key_arn != "" ? var.kms_key_arn : (length(aws_kms_key.iam_encryption) > 0 ? aws_kms_key.iam_encryption[0].arn : null)
}

output "kms_alias_name" {
  description = "Name of the IAM encryption KMS key alias"
  value       = length(aws_kms_alias.iam_encryption) > 0 ? aws_kms_alias.iam_encryption[0].name : null
}

# Logging and Audit
output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group for IAM events"
  value       = aws_cloudwatch_log_group.cloudmart_iam_events.name
}

output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch log group for IAM events"
  value       = aws_cloudwatch_log_group.cloudmart_iam_events.arn
}

output "cloudtrail_arn" {
  description = "ARN of the CloudTrail for IAM audit logging"
  value       = length(aws_cloudtrail.cloudmart_iam_audit) > 0 ? aws_cloudtrail.cloudmart_iam_audit[0].arn : null
}

output "audit_s3_bucket_name" {
  description = "Name of the S3 bucket for audit logs"
  value       = length(aws_s3_bucket.cloudmart_audit_logs) > 0 ? aws_s3_bucket.cloudmart_audit_logs[0].bucket : null
}

output "audit_s3_bucket_arn" {
  description = "ARN of the S3 bucket for audit logs"
  value       = length(aws_s3_bucket.cloudmart_audit_logs) > 0 ? aws_s3_bucket.cloudmart_audit_logs[0].arn : null
}

# Integration Information
output "oidc_provider_arn" {
  description = "ARN of the CloudMart EKS OIDC provider"
  value       = data.aws_iam_openid_connect_provider.cloudmart_oidc.arn
}

output "eks_cluster_name" {
  description = "Name of the CloudMart EKS cluster"
  value       = data.aws_eks_cluster.cloudmart.name
}

output "eks_cluster_arn" {
  description = "ARN of the CloudMart EKS cluster"
  value       = data.aws_eks_cluster.cloudmart.arn
}

# Environment and Configuration
output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "policy_boundary_enabled" {
  description = "Whether policy boundaries are enabled"
  value       = var.enable_policy_boundaries
}

output "mfa_enforcement_enabled" {
  description = "Whether MFA enforcement is enabled"
  value       = var.enable_mfa_enforcement
}

output "audit_logging_enabled" {
  description = "Whether audit logging is enabled"
  value       = var.enable_audit_logging
}

# Role Assumption Commands (for documentation)
output "developer_role_assumption_command" {
  description = "AWS CLI command to assume the developer role"
  value = "aws sts assume-role --role-arn ${aws_iam_role.cloudmart_developer.arn} --role-session-name CloudMart-Developer-Session --external-id <EXTERNAL_ID> --serial-number <MFA_DEVICE_ARN> --token-code <MFA_TOKEN>"
}

output "sre_role_assumption_command" {
  description = "AWS CLI command to assume the SRE role"
  value = "aws sts assume-role --role-arn ${aws_iam_role.cloudmart_sre.arn} --role-session-name CloudMart-SRE-Session --external-id <EXTERNAL_ID> --serial-number <MFA_DEVICE_ARN> --token-code <MFA_TOKEN>"
}

# Kubernetes Service Account Information
output "developer_service_account_name" {
  description = "Kubernetes service account name for developers"
  value       = "cloudmart-developer-sa"
}

output "developer_service_account_namespace" {
  description = "Kubernetes namespace for developer service account"
  value       = var.environment
}

# Compliance and Security Information
output "compliance_controls_enabled" {
  description = "List of enabled compliance controls"
  value = {
    soc2     = var.enable_soc2_controls
    iso27001 = var.enable_iso27001_controls
    pci_dss  = var.enable_pci_dss_controls
  }
}

output "security_features" {
  description = "Summary of security features enabled"
  value = {
    mfa_enforcement    = var.enable_mfa_enforcement
    policy_boundaries  = var.enable_policy_boundaries
    audit_logging     = var.enable_audit_logging
    encryption        = true
    least_privilege   = true
  }
}
