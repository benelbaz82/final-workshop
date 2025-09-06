# -*- coding: utf-8 -*-
# main.py
# Generate architecture diagrams for the Final Workshop:
# 1) AWS - Overall Architecture (ECS/Fargate)
# 2) AWS - Network & Data (Deep Dive)
# 3) CI/CD Pipeline
# 4) Single VM Alternative (Dev/Test)
# 5) CloudFront + WAF in front of ALB (for ECS/Fargate)
# 6) EKS Architecture (ALB Ingress Controller)

from diagrams import Diagram, Cluster, Edge

# On-prem / general
from diagrams.onprem.client import User
from diagrams.onprem.vcs import Github
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.network import Nginx, Apache


# AWS common
from diagrams.aws.network import (
    VPC, PublicSubnet, PrivateSubnet, ALB, InternetGateway, NATGateway, Route53, CloudFront
)
from diagrams.aws.compute import ECS, ECR, Fargate, EC2
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.storage import S3
from diagrams.aws.security import ACM, WAF, Shield, SecretsManager
from diagrams.aws.management import Cloudwatch

# K8s (for EKS detail)
from diagrams.aws.compute import EKS
from diagrams.k8s.network import Ingress, Service
from diagrams.k8s.compute import Pod, Deployment


# ----------------------------------------------------------------
# 1) AWS - Overall Architecture (ECS/Fargate)  [unchanged, refined]
# ----------------------------------------------------------------
with Diagram("AWS - Overall Architecture", filename="aws_overall_architecture", direction="TB", show=False):
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


# ---------------------------------------------------------
# 2) AWS - Network & Data (Deep Dive)   [unchanged, refined]
# ---------------------------------------------------------
with Diagram("AWS - Network & Data (Deep Dive)", filename="aws_network_and_data", direction="TB", show=False):
    with Cluster("VPC"):
        igw = InternetGateway("IGW")

        with Cluster("AZ-a"):
            pub_a = PublicSubnet("Public Subnet a")
            pvt_app_a = PrivateSubnet("Private App Subnet a")
            pvt_data_a = PrivateSubnet("Private Data Subnet a")
            nat_a = NATGateway("NAT GW a")

        with Cluster("AZ-b"):
            pub_b = PublicSubnet("Public Subnet b")
            pvt_app_b = PrivateSubnet("Private App Subnet b")
            pvt_data_b = PrivateSubnet("Private Data Subnet b")
            nat_b = NATGateway("NAT GW b")

        alb = ALB("ALB :443")
        alb - igw
        nat_a - igw
        nat_b - igw

        web_a = Fargate("Web (Gunicorn)")
        web_b = Fargate("Web (Gunicorn)")
        worker_a = Fargate("Worker")
        worker_b = Fargate("Worker")
        scheduler = Fargate("Scheduler")

        rds_primary = RDS("RDS Postgres (Primary)")
        rds_standby = RDS("RDS Postgres (Standby)")
        redis_primary = ElastiCache("Redis (Primary)")
        redis_replica = ElastiCache("Redis (Replica)")

        # Traffic
        alb >> Edge(label=":8000") >> web_a
        alb >> Edge(label=":8000") >> web_b

        # Egress
        for n in [web_a, worker_a, scheduler]:
            n >> nat_a
        for n in [web_b, worker_b]:
            n >> nat_b

        # Data plane
        for n in [web_a, web_b, worker_a, worker_b, scheduler]:
            n >> rds_primary
            n >> redis_primary

        # HA/Replication
        rds_primary - Edge(label="Multi-AZ Sync") - rds_standby
        redis_primary - Edge(label="Replication") - redis_replica


# -----------------
# 3) CI/CD Pipeline
# -----------------
with Diagram("CI/CD Pipeline", filename="cicd_pipeline", direction="LR", show=False):
    dev = User("Developer")
    repo = Github("GitHub Repo\n(main)")
    ci = GithubActions("GitHub Actions\nWorkflow")

    with Cluster("CI"):
        tests = GithubActions("Run Tests")
        build = GithubActions("Build Docker Image")
        push = GithubActions("Push to ECR")

    with Cluster("CD"):
        deploy = GithubActions("Deploy to ECS\n(Rolling Update)")

    registry = ECR("AWS ECR")
    ecs = ECS("ECS Service (Web/Worker/Scheduler)")
    cw = Cloudwatch("CloudWatch\nAlarms on Deploy")

    dev >> Edge(label="git push") >> repo >> ci
    ci >> tests >> build >> push >> deploy
    push >> registry
    deploy >> ecs >> cw


# --------------------------------------
# 4) Single VM Alternative (Dev/Test)
# --------------------------------------
with Diagram("Single VM Alternative (Dev/Test)", filename="single_vm_alternative", direction="TB", show=False):
    user = User("End User")
    with Cluster("Single Linux Server\n(CentOS/Ubuntu)"):
        http = Nginx("Nginx")  # or Apache()
        gunicorn = Server("Gunicorn + Django")
        db = PostgreSQL("PostgreSQL 10+ :5432")
        cache = Redis("Redis 4+ :6379")

    user >> Edge(label="HTTPS 443 / HTTP 8000") >> http >> Edge(label="proxy → 8000") >> gunicorn
    gunicorn >> db
    gunicorn >> cache


# -------------------------------------------------------------
# 5) CloudFront + WAF in front of ALB  (for ECS/Fargate setup)
# -------------------------------------------------------------
with Diagram("CloudFront + WAF + Shield -> ALB (ECS)", filename="cloudfront_fronting_alb", direction="TB", show=False):
    enduser = User("End User")
    r53 = Route53("Route 53")
    waf_edge = WAF("AWS WAF (Global)")
    shield_edge = Shield("AWS Shield Advanced")
    cf = CloudFront("Amazon CloudFront\n(Edge TLS, Caching, OAC)")
    acm_edge = ACM("ACM (us-east-1)\nEdge Cert")
    acm_regional = ACM("ACM (Regional)\nALB Cert")

    with Cluster("AWS Cloud / VPC"):
        alb = ALB("Application Load Balancer\nHTTPS :443")
        with Cluster("ECS Services"):
            web1 = Fargate("Web Task :8000")
            web2 = Fargate("Web Task :8000")
            worker = Fargate("Worker")
            sched = Fargate("Scheduler")

        rds = RDS("RDS PostgreSQL (Multi-AZ)")
        redis = ElastiCache("ElastiCache Redis")

    # Flow: User -> Route53 -> WAF/Shield -> CloudFront -> ALB -> App
    enduser >> Edge(label="DNS") >> r53 >> Edge(label="HTTPS 443") >> waf_edge >> shield_edge >> cf >> alb
    acm_edge >> cf
    acm_regional >> alb

    # ALB to services
    alb >> Edge(label="HTTP 8000") >> web1
    alb >> Edge(label="HTTP 8000") >> web2
    for n in [web1, web2, worker, sched]:
        n >> Edge(label="5432") >> rds
        n >> Edge(label="6379") >> redis


# ------------------------------------------------
# 6) EKS Architecture (ALB Ingress Controller)
# ------------------------------------------------
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import User

from diagrams.aws.network import Route53, CloudFront, ALB
from diagrams.aws.security import WAF, Shield, ACM, SecretsManager
from diagrams.aws.compute import EKS, EC2
from diagrams.aws.database import RDS, ElastiCache

from diagrams.k8s.network import Ingress, Service
from diagrams.k8s.compute import Deployment, Pod

import os
from diagrams import Diagram, Cluster, Edge

# ---- א. תיקון PATH ל-Graphviz ב-Windows (לא מזיק בלינוקס/מק) ----
graphviz_bin = r"C:\Program Files\Graphviz\bin"
if os.name == "nt" and os.path.isdir(graphviz_bin):
    os.environ["PATH"] = graphviz_bin + os.pathsep + os.environ.get("PATH", "")
    os.environ["GRAPHVIZ_DOT"] = os.path.join(graphviz_bin, "dot.exe")

# ---- ב. אייקונים קיימים בלבד (בלי imports לא קיימים) ----


with Diagram(
    "EKS Architecture (ALB Ingress Controller) + Pods + Secrets",
    filename="eks_alb_ingress_with_secrets",
    direction="TB",
    show=False
):
    # שכבת קצה
    user = User("End User")
    r53 = Route53("Route 53 (DNS)")
    waf_edge = WAF("AWS WAF (Global)")
    shield_edge = Shield("AWS Shield Advanced")
    cf = CloudFront("Amazon CloudFront (Edge TLS, Caching)")
    acm_edge = ACM("ACM (us-east-1) - Edge Cert")
    acm_regional = ACM("ACM (Regional) - ALB Cert")
    alb = ALB("Application Load Balancer (Public :443)")

    # שכבת דאטה (מחוץ לקלאסטר)
    with Cluster("Private Data Subnets (Multi-AZ)"):
        rds = RDS("RDS PostgreSQL (Multi-AZ)")
        redis = ElastiCache("ElastiCache Redis (Primary+Replica)")

    # קוברנטיס / EKS
    with Cluster("VPC / EKS"):
        eks = EKS("EKS Control Plane")
        with Cluster("Managed Node Groups (AZ-a / AZ-b)"):
            ng_a = EC2("Node Group a")
            ng_b = EC2("Node Group b")

        with Cluster("Namespace: status-page"):
            # Ingress + Services
            ing = Ingress("Ingress")
            svc_web = Service("Service: web (ClusterIP :8000)")
            svc_rq = Service("Service: rq-worker (ClusterIP)")
            svc_sched = Service("Service: scheduler (ClusterIP)")

            # Deployments
            deploy_web = Deployment("Deployment: web (replicas ≥ 2)")
            deploy_rq = Deployment("Deployment: rq-worker")
            deploy_sched = Deployment("Deployment: scheduler")

            # Pods (מפורטים)
            web_pods = [Pod("web-0"), Pod("web-1")]
            rq_pod = Pod("rq-worker-0")
            sched_pod = Pod("scheduler-0")

            # "Secrets" כ־Pods עם תווית ברורה (כדי שלא נצטרך אייקון שלא קיים)
            k8s_secret_db = Pod("Secret: db-credentials\n(POSTGRES_USER/PASSWORD/HOST/PORT)")
            k8s_secret_redis = Pod("Secret: redis-credentials\n(REDIS_HOST/PORT/PASSWORD)")
            k8s_secret_django = Pod("Secret: django-secret-key\n(SECRET_KEY)")

    # מקור אופציונלי לסודות מחוץ לקלאסטר
    sm = SecretsManager("AWS Secrets Manager\n(db, redis, django)")

    # --- זרימת תנועה Edge -> CF -> ALB -> Ingress -> Service -> Deployment -> Pods ---
    user >> Edge(label="DNS") >> r53 >> Edge(label="HTTPS :443") >> waf_edge >> shield_edge >> cf >> alb
    acm_edge >> cf
    acm_regional >> alb

    alb >> Edge(label="HTTP/HTTPS") >> ing >> svc_web >> deploy_web
    for wp in web_pods:
        deploy_web >> wp

    # Workers/Scheduler - פנימי
    svc_rq >> deploy_rq >> rq_pod
    svc_sched >> deploy_sched >> sched_pod

    # שימוש ב-"Secrets" מתוך הקלאסטר (ייצוג ויזואלי בלבד: envFrom/volume)
    for tgt in [deploy_web, deploy_rq, deploy_sched]:
        k8s_secret_db >> Edge(label="envFrom/volume") >> tgt
        k8s_secret_redis >> Edge(label="envFrom/volume") >> tgt
        k8s_secret_django >> Edge(label="envFrom/volume") >> tgt

    # סנכרון אופציונלי מסיקרטס מנג'ר (בפועל ע״י ESO/CSI Driver)
    sm >> Edge(label="sync (ESO/CSI)") >> k8s_secret_db
    sm >> Edge(label="sync (ESO/CSI)") >> k8s_secret_redis
    sm >> Edge(label="sync (ESO/CSI)") >> k8s_secret_django

    # גישת אפליקציה ל-DB/Redis
    for comp in [deploy_web, deploy_rq, deploy_sched]:
        comp >> Edge(label="TCP 5432") >> rds
        comp >> Edge(label="TCP 6379") >> redis
