# Status Page EKS Deployment

This Helm chart deploys the Status Page application on AWS EKS using managed AWS services.

## Prerequisites

- AWS EKS cluster
- AWS Load Balancer Controller installed in the cluster
- RDS PostgreSQL database
- ElastiCache Redis cluster
- ECR repository with the application image
- Route 53 hosted zone
- AWS Certificate Manager certificate (optional for HTTPS)

## Installation

1. Update the `values.yaml` file with your AWS resource endpoints:

```yaml
aws:
  rds:
    endpoint: "your-rds-endpoint.rds.amazonaws.com"
  redis:
    endpoint: "your-redis-endpoint.cache.amazonaws.com"
  domain: "status.yourdomain.com"
  secretsManager:
    secretArn: "arn:aws:secretsmanager:us-east-1:123456789012:secret:status-page-db-credentials"
```

2. Install the chart:

```bash
helm install status-page ./helm/status-page-eks
```

## Configuration

### AWS Services Integration

The application is configured to use:
- **RDS PostgreSQL**: For database storage
- **ElastiCache Redis**: For caching and background tasks
- **S3 + CloudFront**: For static file serving (configured in Django settings)
- **Secrets Manager**: For database credentials

### Ingress

The ingress uses AWS Load Balancer Controller to create an ALB with:
- HTTPS redirection
- SSL termination
- Path-based routing

### Security

- Service accounts with IAM roles for AWS service access
- Secrets stored in AWS Secrets Manager
- Network policies restrict pod-to-pod communication

## Components

- **Web**: Django application with Gunicorn
- **Worker**: Background task processing with RQ
- **Scheduler**: Periodic task scheduling
- **Ingress**: ALB ingress controller
- **ConfigMap**: Application configuration
- **Secrets**: Database credentials

## Scaling

Adjust replica counts in `values.yaml`:

```yaml
replicaCount: 3  # For web and worker deployments
```

## Monitoring

The Terraform configuration includes optional monitoring services:
- Amazon Managed Prometheus
- Amazon Managed Grafana
- OpenSearch

Enable these in your Terraform deployment for observability.

## Troubleshooting

1. Check pod logs: `kubectl logs -l app=web`
2. Verify AWS service connectivity
3. Check ingress status: `kubectl get ingress`
4. Verify ALB creation in AWS console

## Updating

```bash
helm upgrade status-page ./helm/status-page-eks
```