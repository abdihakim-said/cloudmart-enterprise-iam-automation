variable "environment" {
  description = "Environment name"
  type        = string
}

variable "roles" {
  description = "IAM roles configuration"
  type = map(object({
    assume_role_policy = string
    policies          = list(string)
    max_session_duration = optional(number, 3600)
  }))
}

resource "aws_iam_role" "roles" {
  for_each = var.roles

  name                 = "${each.key}-${var.environment}"
  assume_role_policy   = each.value.assume_role_policy
  max_session_duration = each.value.max_session_duration

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_iam_role_policy_attachment" "role_policies" {
  for_each = {
    for combo in flatten([
      for role_name, role_config in var.roles : [
        for policy in role_config.policies : {
          role_name = role_name
          policy    = policy
        }
      ]
    ]) : "${combo.role_name}-${combo.policy}" => combo
  }

  role       = aws_iam_role.roles[each.value.role_name].name
  policy_arn = each.value.policy
}

output "role_arns" {
  value = { for k, v in aws_iam_role.roles : k => v.arn }
}
