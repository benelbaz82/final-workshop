from diagrams import Diagram, Cluster, Edge
from diagrams.aws.network import VPC, PublicSubnet, PrivateSubnet, ALB, InternetGateway, NATGateway
from diagrams.aws.compute import ECS, ECR, Fargate
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.security import SecretsManager, ACM
from diagrams.aws.management import Cloudwatch
from diagrams.onprem.client import User
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.vcs import Github

with Diagram("ארכיטקטורה כוללת", show=False, filename="overall_architecture", direction="TB"):
    user = User("משתמש")

    with Cluster("AWS Cloud"):
        with Cluster("VPC"):
            igw = InternetGateway("Internet Gateway")
            
            with Cluster("Availability Zone 1"):
                with Cluster("Public Subnet 1"):
                    alb = ALB("Application\nLoad Balancer")
                
                with Cluster("Private App Subnet 1"):
                    ecs_task_1 = Fargate("ECS Task (Fargate)")

                with Cluster("Private Data Subnet 1"):
                    rds_primary = RDS("PostgreSQL DB\n(Primary)")
                    redis_primary = ElastiCache("Redis\n(Primary)")

            with Cluster("Availability Zone 2"):
                with Cluster("Public Subnet 2"):
                    nat = NATGateway("NAT Gateway")
                
                with Cluster("Private App Subnet 2"):
                    ecs_task_2 = Fargate("ECS Task (Fargate)")

                with Cluster("Private Data Subnet 2"):
                    rds_standby = RDS("PostgreSQL DB\n(Standby)")
                    redis_standby = ElastiCache("Redis\n(Standby)")

            # Define relationships within VPC
            alb - Edge(label="HTTPS (443)") - igw
            user >> igw
            
            alb >> Edge(label="HTTP (8000)") >> ecs_task_1
            alb >> Edge(label="HTTP (8000)") >> ecs_task_2
            
            ecs_task_1 >> rds_primary
            ecs_task_2 >> rds_primary
            
            ecs_task_1 >> redis_primary
            ecs_task_2 >> redis_primary
            
            rds_primary - Edge(label="Sync Replication") - rds_standby
            redis_primary - Edge(label="Replication") - redis_standby

            ecs_task_1 >> nat
            ecs_task_2 >> nat
            nat >> igw

        # Other AWS Services
        acm = ACM("Certificate\nManager")
        secrets_manager = SecretsManager("Secrets Manager")
        ecr = ECR("Elastic Container\nRegistry")
        cloudwatch = Cloudwatch("CloudWatch\n(Logs, Metrics, Alarms)")
        
        # Relationships with other services
        acm >> alb
        secrets_manager >> ecs_task_1
        secrets_manager >> ecs_task_2
        ecr << ecs_task_1
        ecr << ecs_task_2
        
        ecs_task_1 >> cloudwatch
        ecs_task_2 >> cloudwatch
        alb >> cloudwatch
        rds_primary >> cloudwatch
        redis_primary >> cloudwatch

with Diagram("CI/CD Pipeline", show=False, filename="cicd_pipeline", direction="LR"):
    github_repo = Github("GitHub Repo\n(main branch)")

    with Cluster("GitHub Actions CI/CD"):
        ci_cd_pipeline = GithubActions("GitHub Actions\nWorkflow")

        with Cluster("CI - Continuous Integration"):
            tests = GithubActions("1. Run Tests")
            build = GithubActions("2. Build Docker Image")
            push_ecr = GithubActions("3. Push to ECR")

        with Cluster("CD - Continuous Deployment"):
            deploy_ecs = GithubActions("4. Deploy to ECS\n(Rolling Update)")

    # Pipeline flow
    github_repo >> Edge(label="Git Push") >> ci_cd_pipeline
    ci_cd_pipeline >> tests >> build >> push_ecr >> deploy_ecs

    # External services in pipeline
    aws_ecr = ECR("AWS ECR")
    aws_ecs = ECS("AWS ECS Service")

    push_ecr >> aws_ecr
    deploy_ecs >> aws_ecs
