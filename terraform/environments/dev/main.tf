terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "iam_roles" {
  source = "../../modules/iam-roles"
  
  environment = "dev"
  roles = {
    developer = {
      assume_role_policy = data.aws_iam_policy_document.developer_assume_role.json
      policies = [
        "arn:aws:iam::aws:policy/PowerUserAccess"
      ]
    }
    readonly = {
      assume_role_policy = data.aws_iam_policy_document.readonly_assume_role.json
      policies = [
        "arn:aws:iam::aws:policy/ReadOnlyAccess"
      ]
    }
  }
}

data "aws_iam_policy_document" "developer_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    condition {
      test     = "Bool"
      variable = "aws:MultiFactorAuthPresent"
      values   = ["true"]
    }
  }
}

data "aws_iam_policy_document" "readonly_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
  }
}

data "aws_caller_identity" "current" {}
