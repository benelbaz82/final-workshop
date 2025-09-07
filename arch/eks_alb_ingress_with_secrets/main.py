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

from diagrams.k8s.network import Ingress, Service
from diagrams.k8s.compute import Deployment, Pod, DaemonSet
from diagrams.k8s.rbac import ServiceAccount

from diagrams.generic.blank import Blank

# ---- A. Fix Graphviz PATH for Windows (harmless on Linux/Mac) ----
graphviz_bin = r"C:\Program Files\Graphviz\bin"
if os.name == "nt" and os.path.isdir(graphviz_bin):
    os.environ["PATH"] = graphviz_bin + os.pathsep + os.environ.get("PATH", "")
    os.environ["GRAPHVIZ_DOT"] = os.path.join(graphviz_bin, "dot.exe")

# ---- B. Only existing icons (no non-existent imports) ----
with Diagram(
    "EKS Architecture (ALB Ingress Controller) + AWS Secrets Manager Integration",
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

    # Data Layer
    with Cluster("Data Layer (Multi-AZ)"):
        rds = RDS("RDS PostgreSQL\n(Multi-AZ)")
        redis = ElastiCache("ElastiCache Redis\n(Multi-AZ)")
        opensearch = AmazonOpensearchService("OpenSearch Service\n(Multi-AZ)")

    # Kubernetes / EKS
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
            # Deployment for scheduler (replicas: 1 for consistent operations)
            deploy_sched = Deployment("scheduler-deployment\n(replicas: 1)")

            # HPA for web pods
            hpa_web = ApplicationAutoScaling("HPA\n(web pods)")

            # Pods
            web_pods = [Pod("web-pod-1"), Pod("web-pod-2")]
            rq_pods = [Pod("rq-pod-1"), Pod("rq-pod-2")]
            sched_pod = Pod("scheduler-pod")

            # AWS Secrets Manager Integration
            sa = ServiceAccount("Service Account (D)\n(IRSA)")
            csi_driver = DaemonSet("Secrets Store CSI Driver (E)\n(AWS ASCP (F))")
            spc = Blank("SecretProviderClass (G)")

    # AWS Secrets Manager
    sm = SecretsManager("AWS Secrets Manager")

    # --- Traffic Flow ---
    user >> r53 >> cf >> alb

    alb >> ing >> svc_web >> deploy_web
    deploy_web >> web_pods[0]
    deploy_web >> web_pods[1]

    deploy_rq >> rq_pods[0]
    deploy_rq >> rq_pods[1]
    deploy_sched >> sched_pod

    # HPA monitoring web pods
    hpa_web >> deploy_web

    # Cluster Autoscaler monitoring nodes
    cluster_autoscaler >> ng_a
    cluster_autoscaler >> ng_b

    # AWS Secrets Manager Integration
    sm >> Edge(label="fetch secrets") >> spc
    spc >> Edge(label="defines") >> csi_driver
    csi_driver >> Edge(label="uses") >> sa
    sa >> Edge(label="permissions") >> deploy_web
    sa >> Edge(label="permissions") >> deploy_rq
    sa >> Edge(label="permissions") >> deploy_sched
    # Secrets mounted to pods
    csi_driver >> Edge(label="mounts secrets") >> web_pods[0]
    csi_driver >> Edge(label="mounts secrets") >> web_pods[1]
    csi_driver >> Edge(label="mounts secrets") >> rq_pods[0]
    csi_driver >> Edge(label="mounts secrets") >> rq_pods[1]
    csi_driver >> Edge(label="mounts secrets") >> sched_pod

    # Application access to DB/Redis/OpenSearch
    deploy_web >> rds
    deploy_web >> redis
    deploy_web >> opensearch
    deploy_rq >> rds
    deploy_rq >> redis
    deploy_rq >> opensearch
    deploy_sched >> rds
    deploy_sched >> redis
    deploy_sched >> opensearch
