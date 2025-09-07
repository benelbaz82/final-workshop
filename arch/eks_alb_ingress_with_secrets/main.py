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
from diagrams.aws.security import SecretsManager
from diagrams.aws.compute import EKS, EC2, ApplicationAutoScaling
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.analytics import AmazonOpensearchService
from diagrams.aws.management import AmazonManagedGrafana, AmazonManagedPrometheus

from diagrams.k8s.network import Ingress, Service
from diagrams.k8s.compute import Deployment, Pod, DaemonSet
from diagrams.k8s.rbac import ServiceAccount, Role
from diagrams.generic.storage import Storage

# ---- A. Fix Graphviz PATH for Windows (harmless on Linux/Mac) ----
graphviz_bin = r"C:\Program Files\Graphviz\bin"
if os.name == "nt" and os.path.isdir(graphviz_bin):
    os.environ["PATH"] = graphviz_bin + os.pathsep + os.environ.get("PATH", "")
    os.environ["GRAPHVIZ_DOT"] = os.path.join(graphviz_bin, "dot.exe")

# ---- B. Only existing icons (no non-existent imports) ----
with Diagram(
    "EKS Architecture with ALB Ingress and Secrets Manager",
    filename="eks_alb_ingress_with_secrets",
    direction="TB",
    show=False,
    node_attr=node_attr
):
    # Edge Layer - User facing components
    with Cluster("Edge Layer"):
        user = User("End User")
        r53 = Route53("Route 53")
        cf = CloudFront("CloudFront")
        alb = ALB("ALB")

    # Kubernetes / EKS - Main application cluster
    with Cluster("EKS Cluster"):
        eks = EKS("Control Plane")

        # Cluster Autoscaler
        cluster_autoscaler = ApplicationAutoScaling("Cluster Autoscaler")

        with Cluster("Node Groups (Auto-Scaling)"):
            ng_a = EC2("Nodes AZ-a")
            ng_b = EC2("Nodes AZ-b")

        with Cluster("status-page Namespace"):
            # Ingress + Service
            ing = Ingress("Ingress")
            svc_web = Service("web-service")

            # Deployments
            deploy_web = Deployment("web-deployment")
            deploy_rq = Deployment("rq-deployment\n(replicas: 2)")
            deploy_sched = Deployment("scheduler-deployment\n(replicas: 1)")

            # HPA for web and RQ pods
            hpa_web = ApplicationAutoScaling("HPA\n(web pods)")
            hpa_rq = ApplicationAutoScaling("HPA\n(RQ pods)")

            # Pods
            web_pods = Pod("Web Pods\n(replicas: 2)")
            rq_pods = Pod("RQ Pods\n(replicas: 2)")
            sched_pod = Pod("Scheduler Pod\n(replicas: 1)")

            # AWS Secrets Manager Integration
            with Cluster("Secrets Integration"):
                sa = ServiceAccount("Service Account\n(IRSA)")
                csi_driver = DaemonSet("Secrets Store CSI Driver\n(AWS ASCP)")
                spc = Role("SecretProviderClass")

    # Data Layer - Databases and storage
    with Cluster("Data Layer (Multi-AZ)"):
        rds = RDS("RDS PostgreSQL\n(Multi-AZ)")
        redis = ElastiCache("ElastiCache Redis\n(Multi-AZ)")
        opensearch = AmazonOpensearchService("OpenSearch Service\n(Multi-AZ)")
        data_access = Storage("Data Access")

    # AWS Secrets Manager - External secrets
    sm = SecretsManager("AWS Secrets Manager")

    # Monitoring & Observability - Observability stack
    with Cluster("Monitoring & Observability"):
        grafana = AmazonManagedGrafana("Amazon Managed Grafana")
        prometheus = AmazonManagedPrometheus("Amazon Managed\nService for Prometheus")

    # --- Traffic Flow ---
    user >> r53 >> cf >> alb >> ing >> svc_web >> deploy_web >> web_pods

    # Application deployments to pods
    deploy_rq >> rq_pods
    deploy_sched >> sched_pod

    # HPA monitoring
    hpa_web >> deploy_web
    hpa_rq >> deploy_rq

    # Cluster Autoscaler
    cluster_autoscaler >> ng_a
    cluster_autoscaler >> ng_b

    # AWS Secrets Manager Integration
    sm >> Edge(label="fetch secrets") >> spc
    spc >> csi_driver >> sa
    sa >> Edge(label="IRSA permissions") >> [deploy_web, deploy_rq, deploy_sched]
    csi_driver >> Edge(label="mount secrets") >> [web_pods, rq_pods, sched_pod]

    # Data access
    [deploy_web, deploy_rq, deploy_sched] >> Edge(label="access data") >> data_access

    # Monitoring
    [deploy_web, deploy_rq, deploy_sched] >> Edge(label="metrics") >> prometheus >> grafana
