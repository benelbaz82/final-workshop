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

# AWS Provider configuration
provider "aws" {
  region = env("MY_AWS_REGION")

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
    Project     = var.project_name
    Environment = "dev"
    owner       = var.owner
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
