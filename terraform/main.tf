variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "final-workshop"
}

variable "owner" {
  description = "Owner of the resources"
  type        = string
  default     = "benami"
}

# For GitHub Actions OIDC
variable "use_oidc_provider" {
  description = "Use OIDC provider for GitHub Actions"
  type        = bool
  default     = false
}

variable "github_org" {
  description = "GitHub organization name"
  type        = string
  default     = "benelbaz82"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "final-workshop"
}

# OIDC Provider for GitHub Actions (if using OIDC)
data "aws_caller_identity" "current" {}

# IAM Role for GitHub Actions (if using OIDC)
resource "aws_iam_role" "github_actions" {
  count = var.use_oidc_provider ? 1 : 0
  name  = "${var.project_name}-github-actions"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:*"
          }
        }
      }
    ]
  })

  tags = {
    Project = var.project_name
    owner = var.owner
  }
}

# Attach ECR permissions to the role
resource "aws_iam_role_policy_attachment" "github_actions_ecr" {
  count      = var.use_oidc_provider ? 1 : 0
  role       = aws_iam_role.github_actions[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess"
}

# AWS Provider configuration
provider "aws" {
  region = var.aws_region

  # Authentication will be done using AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
  # environment variables set in GitHub Actions
}

resource "aws_ecr_repository" "main" {
  name                 = var.project_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project = var.project_name
    Environment = "dev"
    owner = var.owner
  }
}

output "repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.main.repository_url
}

output "repository_arn" {
  description = "ARN of the ECR repository"
  value       = aws_ecr_repository.main.arn
}
