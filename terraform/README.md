# Terraform ECR Setup

This Terraform configuration creates ECR repositories for the final-workshop project.

## Features

- Creates a single ECR repository: `final-workshop`
- Image scanning enabled for security
- Proper tagging and organization with owner tag
- Support for both local development and GitHub Actions CI/CD
- Use different tags for different images (e.g., `app:latest`, `monitor:latest`)

## Configuration Variables

You can customize the following variables in your `terraform.tfvars` file:

- `aws_region`: AWS region (default: "us-east-1")
- `project_name`: Name of the project (default: "final-workshop")
- `owner`: Owner tag for resources (default: "benami")
- `use_oidc_provider`: Enable OIDC for GitHub Actions (default: false)
- `github_org`: GitHub organization (default: "benelbaz82")
- `github_repo`: GitHub repository (default: "final-workshop")

## Usage

### Local Development

1. Copy the example file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` with your AWS credentials:
   ```hcl
   aws_access_key_id     = "your-access-key"
   aws_secret_access_key = "your-secret-key"
   ```

3. Run Terraform:
   ```bash
   cd terraform
   terraform init
   terraform plan
   terraform apply
   ```

### GitHub Actions

The configuration supports two authentication methods:

#### Option 1: AWS Access Keys (Simple)

1. Add these secrets to your GitHub repository:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_ACCOUNT_ID` (your AWS account ID)

2. The GitHub Actions workflow will automatically use these credentials.

#### Option 2: OIDC Provider (Recommended - More Secure)

1. First, create the OIDC provider and IAM role by running Terraform with OIDC enabled:
   ```bash
   # In terraform.tfvars
   use_oidc_provider = true
   ```

2. Apply the Terraform to create the IAM role:
   ```bash
   terraform apply
   ```

3. In GitHub repository settings, add these secrets:
   - `AWS_ACCOUNT_ID` (your AWS account ID)

4. In GitHub repository settings > Variables, add:
   - `USE_OIDC` = `true`

5. The workflow will use OIDC authentication instead of access keys.

## Outputs

After applying, you'll get:
- `repository_url`: ECR repository URL
- `repository_arn`: ARN of the repository

## Usage Examples

### Pushing Images

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <repository_url>

# Tag and push app image
docker tag my-app:latest <repository_url>:app-latest
docker push <repository_url>:app-latest

# Tag and push monitor image
docker tag my-monitor:latest <repository_url>:monitor-latest
docker push <repository_url>:monitor-latest
```

## Security Notes

- Never commit AWS credentials to version control
- Use OIDC when possible for better security
- The IAM role created has minimal required permissions (ECR access only)
- Image scanning is enabled to detect vulnerabilities