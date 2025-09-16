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

variable "domain_name" {
  description = "Domain name for Route 53"
  type        = string
  default     = "statuspage-benami.com"  # Replace with your actual domain
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "statuspage_user"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
  default     = "your_secure_password_here"  # Use Secrets Manager in production
}

variable "eks_version" {
  description = "EKS cluster version"
  type        = string
  default     = "1.28"
}

variable "enable_monitoring" {
  description = "Enable monitoring services (Prometheus, Grafana, OpenSearch)"
  type        = bool
  default     = false  # Set to true if you have permissions
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
# IAM Roles for EKS
########################
resource "aws_iam_role" "eks_cluster" {
  name = "${var.project_name}-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

resource "aws_iam_role" "eks_node_group" {
  name = "${var.project_name}-eks-node-group-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_node_group_policies" {
  for_each = toset([
    "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  ])
  policy_arn = each.value
  role       = aws_iam_role.eks_node_group.name
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
# EKS Cluster
########################
resource "aws_eks_cluster" "main" {
  name     = "${var.project_name}-eks"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = var.eks_version

  vpc_config {
    subnet_ids = concat(values(aws_subnet.public)[*].id, values(aws_subnet.private)[*].id)
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy
  ]

  tags = {
    Name = "${var.project_name}-eks"
  }
}

########################
# EKS Node Group
########################
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.project_name}-node-group"
  node_role_arn   = aws_iam_role.eks_node_group.arn
  subnet_ids      = values(aws_subnet.private)[*].id  # Private subnets for security

  scaling_config {
    desired_size = 3
    max_size     = 5
    min_size     = 1
  }

  instance_types = ["t3.large"]  # As per cost table
  capacity_type  = "ON_DEMAND"

  depends_on = [
    aws_iam_role_policy_attachment.eks_node_group_policies
  ]

  tags = {
    Name = "${var.project_name}-node-group"
  }
}

########################
# ECR
########################
resource "aws_ecr_repository" "main" {
  name                 = "${var.project_name}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

########################
# Security Groups
########################
resource "aws_security_group" "rds" {
  name   = "${var.project_name}-rds-sg"
  vpc_id = aws_vpc.this.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]  # Allow from VPC; restrict further if needed
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-rds-sg"
  }
}

resource "aws_security_group" "redis" {
  name   = "${var.project_name}-redis-sg"
  vpc_id = aws_vpc.this.id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]  # Allow from VPC; restrict further if needed
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-redis-sg"
  }
}

########################
# RDS PostgreSQL (Multi-AZ)
########################
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = values(aws_subnet.private)[*].id

  tags = {
    Name = "${var.project_name}-db-subnet-group"
  }
}

resource "aws_db_instance" "postgres" {
  identifier             = "${var.project_name}-postgres"
  engine                 = "postgres"
  engine_version         = "13"  # As per SAD
  instance_class         = "db.t3.medium"
  allocated_storage      = 100  # As per cost table
  storage_type           = "gp3"
  multi_az               = true  # Multi-AZ for high availability
  db_name                = "statuspage"  # Example; adjust as needed
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  skip_final_snapshot    = true  # For dev; set to false in prod

  tags = {
    Name = "${var.project_name}-postgres"
  }
}

########################
# ElastiCache Redis
########################
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-redis-subnet-group"
  subnet_ids = values(aws_subnet.private)[*].id

  tags = {
    Name = "${var.project_name}-redis-subnet-group"
  }
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.project_name}-redis"
  description                = "Redis replication group for Status-Page"
  node_type                  = "cache.t3.small"
  num_cache_clusters         = 2  # As per cost table
  parameter_group_name       = "default.redis7"
  subnet_group_name          = aws_elasticache_subnet_group.main.name
  security_group_ids         = [aws_security_group.redis.id]
  automatic_failover_enabled = true
  multi_az_enabled          = true

  tags = {
    Name = "${var.project_name}-redis"
  }
}

########################
# S3 + CloudFront
########################
resource "aws_s3_bucket" "main" {
  bucket        = "${var.project_name}-bucket"
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
  name                              = "benami-54155d-oac"
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
# Secrets Manager
########################
resource "aws_secretsmanager_secret" "db_credentials" {
  name = "${var.project_name}-db-credentials"
  description = "Database credentials for Status-Page application"
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
    host     = aws_db_instance.postgres.endpoint
    port     = 5432
    dbname   = aws_db_instance.postgres.db_name
  })
}

########################
# Route 53
########################
resource "aws_route53_zone" "main" {
  name = var.domain_name
  tags = {
    Name = "${var.project_name}-hosted-zone"
  }
}

resource "aws_route53_record" "cloudfront" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "status.${var.domain_name}"
  type    = "CNAME"
  ttl     = 300
  records = [aws_cloudfront_distribution.main.domain_name]
}

########################
# Amazon Managed Prometheus
########################
resource "aws_prometheus_workspace" "main" {
  count = var.enable_monitoring ? 1 : 0
  alias = "${var.project_name}-prometheus"
  tags = {
    Name = "${var.project_name}-prometheus"
  }
}

########################
# Amazon Managed Grafana
########################
resource "aws_grafana_workspace" "main" {
  count = var.enable_monitoring ? 1 : 0
  name        = "${var.project_name}-grafana"
  description = "Managed Grafana workspace for Status-Page monitoring"
  account_access_type      = "CURRENT_ACCOUNT"
  authentication_providers = ["AWS_SSO"]
  permission_type          = "SERVICE_MANAGED"
  role_arn                 = aws_iam_role.grafana[0].arn

  tags = {
    Name = "${var.project_name}-grafana"
  }
}

resource "aws_iam_role" "grafana" {
  count = var.enable_monitoring ? 1 : 0
  name = "${var.project_name}-grafana-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "grafana.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "grafana" {
  count = var.enable_monitoring ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonGrafanaServiceRole"
  role       = aws_iam_role.grafana[0].name
}

########################
# OpenSearch
########################
resource "aws_opensearch_domain" "main" {
  count = var.enable_monitoring ? 1 : 0
  domain_name    = "${var.project_name}-opensearch"
  engine_version = "OpenSearch_2.11"

  cluster_config {
    instance_type          = "t3.small.search"
    instance_count         = 1
    zone_awareness_enabled = false
  }

  ebs_options {
    ebs_enabled = true
    volume_size = 10
    volume_type = "gp3"
  }

  vpc_options {
    subnet_ids         = [values(aws_subnet.private)[0].id]
    security_group_ids = [aws_security_group.rds.id]  # Reuse RDS security group for simplicity
  }

  encrypt_at_rest {
    enabled = true
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  tags = {
    Name = "${var.project_name}-opensearch"
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

output "eks_cluster_name" {
  value = aws_eks_cluster.main.name
}

output "eks_cluster_endpoint" {
  value = aws_eks_cluster.main.endpoint
}

output "node_group_name" {
  value = aws_eks_node_group.main.node_group_name
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "redis_endpoint" {
  value = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "secrets_manager_arn" {
  value = aws_secretsmanager_secret.db_credentials.arn
}

output "route53_zone_id" {
  value = aws_route53_zone.main.zone_id
}

output "route53_nameservers" {
  value = aws_route53_zone.main.name_servers
}

output "prometheus_workspace_arn" {
  value = var.enable_monitoring ? aws_prometheus_workspace.main[0].arn : null
}

output "grafana_workspace_endpoint" {
  value = var.enable_monitoring ? aws_grafana_workspace.main[0].endpoint : null
}

output "opensearch_domain_endpoint" {
  value = var.enable_monitoring ? aws_opensearch_domain.main[0].endpoint : null
}
