########################
# Terraform Configuration
########################
terraform {
  backend "s3" {
    bucket = "benami-terrfrom-remote-state"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}

########################
# Variables
########################
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

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "azs" {
  description = "Availability Zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

########################
# Provider
########################
provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project = var.project_name
      Owner   = var.owner
      Env     = "production"
    }
  }
}

########################
# Data Sources
########################
data "aws_caller_identity" "current" {}

locals {
  az_map = { for idx, az in var.azs : tostring(idx) => az }
}

########################
# Random suffix (for unique names)
########################
resource "random_id" "suffix" {
  byte_length = 3
}

########################
# VPC
########################
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags                 = { Name = "${var.project_name}-vpc" }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.project_name}-igw" }
}

########################
# Subnets
########################
resource "aws_subnet" "public" {
  for_each                = local.az_map
  vpc_id                  = aws_vpc.this.id
  availability_zone       = each.value
  map_public_ip_on_launch = true
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, tonumber(each.key)) # /20
  tags = {
    Name = "${var.project_name}-public-${each.value}"
    Tier = "public"
  }
}

resource "aws_subnet" "private" {
  for_each          = local.az_map
  vpc_id            = aws_vpc.this.id
  availability_zone = each.value
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, 8 + tonumber(each.key)) # /20
  tags = {
    Name = "${var.project_name}-private-${each.value}"
    Tier = "private"
  }
}

########################
# NAT Gateways
########################
resource "aws_eip" "nat" {
  for_each = aws_subnet.public
  domain   = "vpc"
  tags     = { Name = "${var.project_name}-nat-eip-${each.key}" }
}

resource "aws_nat_gateway" "nat" {
  for_each      = aws_subnet.public
  allocation_id = aws_eip.nat[each.key].id
  subnet_id     = each.value.id
  depends_on    = [aws_internet_gateway.igw]
  tags          = { Name = "${var.project_name}-nat-${each.key}" }
}

########################
# Route Tables
########################
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.project_name}-public-rt" }
}

resource "aws_route" "public_igw" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.igw.id
}

resource "aws_route_table_association" "public_assoc" {
  for_each       = aws_subnet.public
  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  for_each = local.az_map
  vpc_id   = aws_vpc.this.id
  tags     = { Name = "${var.project_name}-private-rt-${each.value}" }
}

resource "aws_route" "private_nat" {
  for_each               = local.az_map
  route_table_id         = aws_route_table.private[each.key].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.nat[each.key].id
}

resource "aws_route_table_association" "private_assoc" {
  for_each       = local.az_map
  subnet_id      = aws_subnet.private[each.key].id
  route_table_id = aws_route_table.private[each.key].id
}

########################
# ECR
########################
resource "aws_ecr_repository" "main" {
  name                 = "${var.project_name}-${random_id.suffix.hex}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

########################
# S3 + CloudFront
########################
resource "aws_s3_bucket" "main" {
  bucket        = "${var.project_name}-${random_id.suffix.hex}-bucket"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "main" {
  bucket                  = aws_s3_bucket.main.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_control" "main" {
  name                              = "${var.project_name}-${random_id.suffix.hex}-oac"
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
}

########################
# Outputs
########################
output "caller_identity" {
  value = data.aws_caller_identity.current.arn
}

output "vpc_id" {
  value = aws_vpc.this.id
}

output "public_subnets" {
  value = [for _, s in aws_subnet.public : s.id]
}

output "private_subnets" {
  value = [for _, s in aws_subnet.private : s.id]
}

output "nat_gateway_ids" {
  value = [for _, n in aws_nat_gateway.nat : n.id]
}

output "internet_gateway" {
  value = aws_internet_gateway.igw.id
}

output "ecr_repository_url" {
  value = aws_ecr_repository.main.repository_url
}

output "s3_bucket_name" {
  value = aws_s3_bucket.main.bucket
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.main.domain_name
}
