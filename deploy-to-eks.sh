# EKS Deployment Script for Status Page

#!/bin/bash

# This script helps deploy the Status Page application to AWS EKS
# Make sure you have:
# - AWS CLI configured
# - kubectl configured to access your EKS cluster
# - Helm installed

set -e

echo "🚀 Starting Status Page EKS Deployment"

# Variables - Update these with your actual values
EKS_CLUSTER_NAME="benami-eks"
REGION="us-east-1"
NAMESPACE="default"

# Get Terraform outputs (assuming terraform output is available)
echo "📋 Getting Terraform outputs..."
RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
REDIS_ENDPOINT=$(terraform output -raw redis_endpoint)
SECRETS_ARN=$(terraform output -raw secrets_manager_arn)
DOMAIN="status.statuspage-benami.com"

echo "RDS Endpoint: $RDS_ENDPOINT"
echo "Redis Endpoint: $REDIS_ENDPOINT"
echo "Secrets ARN: $SECRETS_ARN"

# Update Helm values
echo "📝 Updating Helm values..."
cat > helm/status-page-eks/custom-values.yaml << EOF
aws:
  rds:
    endpoint: "$RDS_ENDPOINT"
  redis:
    endpoint: "$REDIS_ENDPOINT"
  domain: "$DOMAIN"
  secretsManager:
    secretArn: "$SECRETS_ARN"

# Add other customizations here
EOF

# Install AWS Load Balancer Controller if not already installed
echo "🔧 Installing AWS Load Balancer Controller..."
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
  --set clusterName=$EKS_CLUSTER_NAME \
  --set serviceAccount.create=true \
  --set serviceAccount.name=aws-load-balancer-controller \
  --namespace kube-system

# Wait for ALB controller to be ready
echo "⏳ Waiting for ALB controller to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/aws-load-balancer-controller -n kube-system

# Install the application
echo "📦 Installing Status Page application..."
helm upgrade --install status-page ./helm/status-page-eks \
  --values ./helm/status-page-eks/custom-values.yaml \
  --namespace $NAMESPACE \
  --create-namespace

# Wait for deployments to be ready
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=600s deployment/web -n $NAMESPACE
kubectl wait --for=condition=available --timeout=600s deployment/worker -n $NAMESPACE
kubectl wait --for=condition=available --timeout=600s deployment/scheduler -n $NAMESPACE

# Get the ALB DNS name
echo "🌐 Getting ALB information..."
ALB_DNS=$(kubectl get ingress status-page-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' -n $NAMESPACE)
echo "ALB DNS: $ALB_DNS"

# Update Route 53 (manual step required)
echo "📋 Manual steps required:"
echo "1. Create/update Route 53 CNAME record for $DOMAIN pointing to $ALB_DNS"
echo "2. Request ACM certificate for $DOMAIN if not already done"
echo "3. Update ingress annotations with certificate ARN"

echo "✅ Deployment completed!"
echo "🌍 Your Status Page will be available at: https://$DOMAIN"