# -*- coding: utf-8 -*-
# main.py
# Generate architecture diagrams for the Final Workshop:
# 6) EKS Architecture (ALB Ingress Controller)

from diagrams import Diagram, Cluster, Edge
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from settings import node_attr

from diagrams.onprem.client import User

from diagrams.aws.network import Route53, CloudFront, ALB
from diagrams.aws.security import WAF, Shield, ACM, SecretsManager, IAM
from diagrams.aws.compute import EKS, EC2, ApplicationAutoScaling
from diagrams.aws.database import RDS, ElastiCache

from diagrams.k8s.network import Ingress, Service
from diagrams.k8s.compute import Deployment, Pod
from diagrams.k8s.podconfig import Secret

# ---- A. Fix Graphviz PATH for Windows (harmless on Linux/Mac) ----
graphviz_bin = r"C:\Program Files\Graphviz\bin"
if os.name == "nt" and os.path.isdir(graphviz_bin):
    os.environ["PATH"] = graphviz_bin + os.pathsep + os.environ.get("PATH", "")
    os.environ["GRAPHVIZ_DOT"] = os.path.join(graphviz_bin, "dot.exe")

# ---- B. Only existing icons (no non-existent imports) ----
with Diagram(
    "EKS Architecture (ALB Ingress Controller) + Pods + Secrets",
    filename="eks_alb_ingress_with_secrets",
    direction="TB",
    show=False,
    node_attr=node_attr
):
    # Edge Layer - grouped into cluster
    with Cluster("Edge Layer"):
        user = User("End User")
        r53 = Route53("Route 53")
        cf = CloudFront("CloudFront")
        alb = ALB("ALB")

        # Security components
        waf_edge = WAF("WAF")
        shield_edge = Shield("Shield")
        acm_edge = ACM("ACM Edge")
        acm_regional = ACM("ACM Regional")

    # Data Layer
    with Cluster("Data Layer (Multi-AZ)"):
        rds = RDS("RDS PostgreSQL\n(Multi-AZ)")
        redis = ElastiCache("ElastiCache Redis\n(Multi-AZ)")

    # Kubernetes / EKS
    with Cluster("EKS Cluster"):
        eks = EKS("Control Plane")

        # Cluster Autoscaler
        cluster_autoscaler = ApplicationAutoScaling("Cluster Autoscaler")

        with Cluster("Node Groups (Auto-Scaling)"):
            ng_a = EC2("Nodes AZ-a")
            ng_b = EC2("Nodes AZ-b")

        with Cluster("status-page Namespace"):
            # IRSA - IAM Roles for Service Accounts
            irsa = IAM("IRSA\n(IAM Roles for Service Accounts)")

            # Ingress + Services
            ing = Ingress("Ingress")
            svc_web = Service("web-service")
            svc_rq = Service("rq-service")
            svc_sched = Service("scheduler-service")

            # Deployments
            deploy_web = Deployment("web-deployment")
            deploy_rq = Deployment("rq-deployment\n(replicas: 2)")
            # Deployment for scheduler (replicas: 1 for consistent operations)
            deploy_sched = Deployment("scheduler-deployment\n(replicas: 1)")

            # HPA for web pods
            hpa_web = ApplicationAutoScaling("HPA\n(web pods)")

            # Pods
            web_pods = [Pod("web-pod-1"), Pod("web-pod-2")]
            rq_pods = [Pod("rq-pod-1"), Pod("rq-pod-2")]
            sched_pod = Pod("scheduler-pod")

            # Secrets
            with Cluster("Kubernetes Secrets"):
                k8s_secret_db = Secret("db-secret")
                k8s_secret_redis = Secret("redis-secret")
                k8s_secret_django = Secret("django-secret")

    # AWS Secrets Manager
    sm = SecretsManager("AWS Secrets Manager")

    # --- Traffic Flow ---
    user >> r53 >> cf >> alb
    cf >> waf_edge
    cf >> shield_edge
    cf >> acm_edge
    alb >> acm_regional

    alb >> ing >> svc_web >> deploy_web
    deploy_web >> web_pods[0]
    deploy_web >> web_pods[1]

    svc_rq >> deploy_rq >> rq_pods[0]
    svc_rq >> deploy_rq >> rq_pods[1]
    svc_sched >> deploy_sched >> sched_pod

    # HPA monitoring web pods
    hpa_web >> deploy_web

    # Cluster Autoscaler monitoring nodes
    cluster_autoscaler >> ng_a
    cluster_autoscaler >> ng_b

    # Secrets connections
    k8s_secret_db >> Edge(label="env") >> deploy_web
    k8s_secret_redis >> Edge(label="env") >> deploy_web
    k8s_secret_django >> Edge(label="env") >> deploy_web

    k8s_secret_db >> Edge(label="env") >> deploy_rq
    k8s_secret_redis >> Edge(label="env") >> deploy_rq
    k8s_secret_django >> Edge(label="env") >> deploy_rq

    k8s_secret_db >> Edge(label="env") >> deploy_sched
    k8s_secret_redis >> Edge(label="env") >> deploy_sched
    k8s_secret_django >> Edge(label="env") >> deploy_sched

    # Sync from AWS Secrets Manager
    sm >> Edge(label="sync") >> k8s_secret_db
    sm >> Edge(label="sync") >> k8s_secret_redis
    sm >> Edge(label="sync") >> k8s_secret_django

    # Application access to DB/Redis
    deploy_web >> rds
    deploy_web >> redis
    deploy_rq >> rds
    deploy_rq >> redis
    deploy_sched >> rds
    deploy_sched >> redis

    # IRSA connections
    irsa >> Edge(label="IAM role") >> deploy_web
    irsa >> Edge(label="IAM role") >> deploy_rq
    irsa >> Edge(label="IAM role") >> deploy_sched
