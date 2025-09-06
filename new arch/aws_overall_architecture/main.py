# -*- coding: utf-8 -*-
# main.py
# Generate architecture diagrams for the Final Workshop:
# 1) AWS - Overall Architecture (ECS/Fargate)

from diagrams import Diagram, Cluster, Edge
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from settings import node_attr
import os
# ---- Fix for Graphviz on Windows ----
graphviz_bin = r"C:\Program Files\Graphviz\bin"
if os.name == "nt" and os.path.isdir(graphviz_bin):
    os.environ["PATH"] = graphviz_bin + os.pathsep + os.environ.get("PATH", "")
    os.environ["GRAPHVIZ_DOT"] = os.path.join(graphviz_bin, "dot.exe")

# On-prem / general
from diagrams.onprem.client import User

# AWS common
from diagrams.aws.network import (
    VPC, PublicSubnet, PrivateSubnet, ALB, InternetGateway, NATGateway, Route53, CloudFront
)
from diagrams.aws.compute import ECS, ECR, Fargate
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.storage import S3
from diagrams.aws.security import ACM, WAF, Shield, SecretsManager
from diagrams.aws.management import Cloudwatch

# ----------------------------------------------------------------
# 1) AWS - Overall Architecture (ECS/Fargate)  [unchanged, refined]
# ----------------------------------------------------------------
with Diagram("AWS - Overall Architecture", filename="aws_overall_architecture", direction="TB", show=False, node_attr=node_attr):
    user = User("End User")

    dns = Route53("Route 53")
    waf = WAF("AWS WAF")
    shield = Shield("AWS Shield")
    acm = ACM("AWS Certificate Manager")

    with Cluster("AWS Cloud"):
        with Cluster("VPC"):
            igw = InternetGateway("Internet Gateway")

            with Cluster("Public Subnets (AZ-a / AZ-b)"):
                alb = ALB("Application Load Balancer\nHTTPS :443 / HTTP :80")
                nat_a = NATGateway("NAT GW (AZ-a)")
                nat_b = NATGateway("NAT GW (AZ-b)")

            with Cluster("Private App Subnets (AZ-a / AZ-b)"):
                with Cluster("ECS Service: Web"):
                    web_a = Fargate("Web Task (Gunicorn)\n:8000")
                    web_b = Fargate("Web Task (Gunicorn)\n:8000")
                with Cluster("ECS Service: RQ Worker"):
                    worker_a = Fargate("Worker Task")
                    worker_b = Fargate("Worker Task")
                with Cluster("ECS Service: Scheduler"):
                    scheduler = Fargate("Scheduler Task")

            with Cluster("Private Data Subnets (Multi-AZ)"):
                rds = RDS("RDS PostgreSQL\n(Multi-AZ)")
                redis = ElastiCache("ElastiCache Redis\n(Primary+Replica)")

        secrets = SecretsManager("Secrets Manager\n(DB creds, SECRET_KEY)")
        logs_metrics = Cloudwatch("CloudWatch\nLogs, Metrics, Alarms")
        ecr = ECR("Elastic Container Registry")
        s3_logs = S3("S3 (ALB Access Logs)")
        s3_static = S3("S3 (Static/Media)\n(optional)")

    # External flow
    user >> Edge(label="DNS") >> dns >> Edge(label="HTTPS 443") >> waf >> shield >> alb
    acm >> alb

    # ALB <-> App
    alb >> Edge(label="HTTP 8000") >> web_a
    alb >> Edge(label="HTTP 8000") >> web_b

    # App -> Data
    for n in [web_a, web_b, worker_a, worker_b, scheduler]:
        n >> Edge(label="TCP 5432") >> rds
        n >> Edge(label="TCP 6379") >> redis

    # Egress
    web_a >> nat_a >> igw
    worker_a >> nat_a
    scheduler >> nat_a
    web_b >> nat_b >> igw
    worker_b >> nat_b

    # Observability & Secrets
    for n in [web_a, web_b, worker_a, worker_b, scheduler, alb, rds, redis]:
        n >> logs_metrics
    for n in [web_a, web_b, worker_a, worker_b, scheduler]:
        secrets >> n
        ecr << n
        n >> s3_static
    alb >> s3_logs
