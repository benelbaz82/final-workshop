# -*- coding: utf-8 -*-
# main.py
# Generate architecture diagrams for the Final Workshop:
# 5) CloudFront + WAF in front of ALB (for ECS/Fargate)

from diagrams import Diagram, Cluster, Edge
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from settings import node_attr

# On-prem / general
from diagrams.onprem.client import User

# AWS common
from diagrams.aws.network import (
    VPC, ALB, Route53, CloudFront
)
from diagrams.aws.compute import Fargate
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.security import ACM, WAF, Shield

# -------------------------------------------------------------
# 5) CloudFront + WAF in front of ALB  (for ECS/Fargate setup)
# -------------------------------------------------------------
with Diagram("CloudFront + WAF + Shield -> ALB (ECS)", filename="cloudfront_fronting_alb", direction="TB", show=False, node_attr=node_attr):
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
