# IAM Automation Module Variables
# Extends CloudMart variable patterns

variable "environment" {
  description = "Environment name (dev, qa, staging, prod)"
  type        = string
  validation {
    condition = contains(["dev", "qa", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, qa, staging, prod."
  }
}

variable "trusted_principals" {
  description = "List of trusted AWS principals that can assume roles"
  type        = list(string)
  default     = []
}

variable "external_id" {
  description = "External ID for role assumption (security best practice)"
  type        = string
  sensitive   = true
}

variable "allowed_regions" {
  description = "List of AWS regions where resources can be created"
  type        = list(string)
  default     = ["us-east-1", "us-west-2"]
}

variable "kms_key_arn" {
  description = "ARN of existing KMS key for encryption (from CloudMart security module)"
  type        = string
  default     = ""
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 90
  validation {
    condition = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch Logs retention period."
  }
}

variable "enable_audit_logging" {
  description = "Enable CloudTrail audit logging for IAM events"
  type        = bool
  default     = true
}

variable "enable_mfa_enforcement" {
  description = "Enforce MFA for all role assumptions"
  type        = bool
  default     = true
}

variable "enable_policy_boundaries" {
  description = "Enable IAM policy boundaries for additional security"
  type        = bool
  default     = true
}

variable "tags" {
  description = "A map of tags to assign to resources (extends CloudMart tagging)"
  type        = map(string)
  default     = {}
}

# Developer role configuration
variable "developer_max_session_duration" {
  description = "Maximum session duration for developer role (seconds)"
  type        = number
  default     = 3600
  validation {
    condition = var.developer_max_session_duration >= 3600 && var.developer_max_session_duration <= 43200
    error_message = "Session duration must be between 1 hour (3600) and 12 hours (43200)."
  }
}

variable "developer_mfa_age_limit" {
  description = "Maximum age of MFA token for developer role (seconds)"
  type        = number
  default     = 3600
}

# SRE role configuration
variable "sre_max_session_duration" {
  description = "Maximum session duration for SRE role (seconds)"
  type        = number
  default     = 14400
  validation {
    condition = var.sre_max_session_duration >= 3600 && var.sre_max_session_duration <= 43200
    error_message = "Session duration must be between 1 hour (3600) and 12 hours (43200)."
  }
}

variable "sre_mfa_age_limit" {
  description = "Maximum age of MFA token for SRE role (seconds)"
  type        = number
  default     = 900
}

# DBA role configuration
variable "dba_max_session_duration" {
  description = "Maximum session duration for DBA role (seconds)"
  type        = number
  default     = 7200
}

variable "dba_mfa_age_limit" {
  description = "Maximum age of MFA token for DBA role (seconds)"
  type        = number
  default     = 1800
}

# Security auditor role configuration
variable "security_auditor_max_session_duration" {
  description = "Maximum session duration for security auditor role (seconds)"
  type        = number
  default     = 3600
}

variable "security_auditor_mfa_age_limit" {
  description = "Maximum age of MFA token for security auditor role (seconds)"
  type        = number
  default     = 3600
}

# Compliance settings
variable "enable_soc2_controls" {
  description = "Enable SOC2 compliance controls"
  type        = bool
  default     = true
}

variable "enable_iso27001_controls" {
  description = "Enable ISO27001 compliance controls"
  type        = bool
  default     = true
}

variable "enable_pci_dss_controls" {
  description = "Enable PCI-DSS compliance controls"
  type        = bool
  default     = false
}

# Integration with existing CloudMart infrastructure
variable "cloudmart_cluster_name" {
  description = "Name of the existing CloudMart EKS cluster"
  type        = string
  default     = "cloudmart-cluster"
}

variable "cloudmart_vpc_id" {
  description = "VPC ID of the existing CloudMart infrastructure"
  type        = string
  default     = ""
}

variable "cloudmart_dynamodb_tables" {
  description = "List of existing CloudMart DynamoDB table names"
  type        = list(string)
  default     = ["cloudmart-products", "cloudmart-orders", "cloudmart-tickets"]
}

# Notification settings
variable "notification_email" {
  description = "Email address for IAM-related notifications"
  type        = string
  default     = ""
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for IAM alerts"
  type        = string
  default     = ""
  sensitive   = true
}
