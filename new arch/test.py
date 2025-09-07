from diagrams import Diagram, Cluster
from diagrams.aws.compute import EKS
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.devtools import Codecommit, Codepipeline, Codebuild
from diagrams.aws.compute import ECR
from diagrams.aws.network import VPC, ALB
from diagrams.aws.management import Cloudwatch
from diagrams.k8s.compute import Deployment
from diagrams.k8s.network import Ingress, Service
from diagrams.onprem.iac import Terraform
from diagrams.onprem.client import User

# הגדרות עיצוב לתרשים
graph_attr = {
    "fontsize": "12",
    "bgcolor": "transparent",
    "splines": "ortho", # שימוש בקווים ישרים לחיבורים
}

with Diagram("ארכיטקטורת פרויקט Status-Page על AWS EKS", show=False, direction="LR", graph_attr=graph_attr, filename="status_page_architecture"):

    # שחקנים חיצוניים
    developer = User("מפתח")
    terraform = Terraform("Terraform (IaC)")

    with Cluster("AWS Cloud"):
        
        # קלאסטר CI/CD
        with Cluster("CI/CD Pipeline"):
            codecommit = Codecommit("CodeCommit Repo")
            codepipeline = Codepipeline("CodePipeline")
            codebuild = Codebuild("CodeBuild")
            ecr = ECR("ECR Registry")

            # זרימת CI/CD
            codecommit >> codepipeline >> codebuild >> ecr
            ecr >> codepipeline

        # קלאסטר VPC ראשי
        with Cluster("VPC"):
            alb = ALB("Application Load Balancer")

            # קלאסטר EKS
            with Cluster("Amazon EKS Cluster"):
                eks_control_plane = EKS("EKS Control Plane")
                
                with Cluster("Worker Nodes"):
                    with Cluster("Kubernetes Resources"):
                        ingress = Ingress("Ingress")
                        service = Service("Service")
                        deployment = Deployment("Deployment\n(Status-Page Pods)")
                        
                        # זרימת תעבורה בתוך הקלאסטר
                        ingress >> service >> deployment
            
            # קלאסטר בסיסי נתונים מנוהלים
            with Cluster("Managed Databases (Private Subnet)"):
                rds_postgres = RDS("RDS for PostgreSQL")
                elasticache_redis = ElastiCache("ElastiCache for Redis")

            # חיבור האפליקציה לבסיסי הנתונים
            deployment >> rds_postgres
            deployment >> elasticache_redis

        # קלאסטר ניטור
        with Cluster("Observability"):
            cloudwatch = Cloudwatch("CloudWatch\n(Container Insights)")
            
        # חיבורים עיקריים
        developer >> codecommit
        codepipeline >> eks_control_plane
        alb >> ingress
        eks_control_plane >> cloudwatch

    # חיבור Terraform לרכיבים שהוא מקים
    terraform >> codecommit
    terraform >> ecr
    terraform >> eks_control_plane
    terraform >> rds_postgres
    terraform >> elasticache_redis
