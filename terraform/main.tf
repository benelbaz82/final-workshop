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

variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
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
    Project     = var.project_name
    Environment = "dev"
    owner       = var.owner
  }
}