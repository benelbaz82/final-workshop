variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "benami"
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
}

##################################
# ECR Repository
##################################
resource "aws_ecr_repository" "main" {
  name                 = var.project_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project     = var.project_name
    Environment = "production"
    Owner       = var.owner
  }
}

##################################
# S3 Bucket (for static files)
##################################
resource "aws_s3_bucket" "main" {
  bucket        = "${var.project_name}-bucket"
  force_destroy = true

  tags = {
    Project     = var.project_name
    Environment = "production"
    Owner       = var.owner
  }
}

# Block public access to the bucket
resource "aws_s3_bucket_public_access_block" "main" {
  bucket                  = aws_s3_bucket.main.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

##################################
# CloudFront Distribution
##################################
resource "aws_cloudfront_origin_access_control" "main" {
  name                              = "${var.project_name}-oac"
  description                       = "OAC for CloudFront to access S3"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  default_root_object = "index.html"

  origin {
    domain_name              = aws_s3_bucket.main.bucket_regional_domain_name
    origin_id                = "s3-origin"
    origin_access_control_id = aws_cloudfront_origin_access_control.main.id
  }

  default_cache_behavior {
    target_origin_id       = "s3-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Project     = var.project_name
    Environment = "production"
    Owner       = var.owner
  }
}

##################################
# Outputs
##################################
output "ecr_repository_url" {
  value = aws_ecr_repository.main.repository_url
}

output "s3_bucket_name" {
  value = aws_s3_bucket.main.bucket
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.main.domain_name
}
