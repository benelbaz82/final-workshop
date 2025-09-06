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
from diagrams.aws.security import WAF, Shield, ACM, SecretsManager
from diagrams.aws.compute import EKS, EC2
from diagrams.aws.database import RDS, ElastiCache

from diagrams.k8s.network import Ingress, Service
from diagrams.k8s.compute import Deployment, Pod

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
    show=False,
    node_attr=node_attr
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
