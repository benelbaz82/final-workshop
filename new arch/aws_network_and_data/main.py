# -*- coding: utf-8 -*-
# main.py
# Generate architecture diagrams for the Final Workshop:
# 2) AWS - Network & Data (Deep Dive)

from diagrams import Diagram, Cluster, Edge
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from settings import node_attr

# AWS common
from diagrams.aws.network import (
    VPC, PublicSubnet, PrivateSubnet, ALB, InternetGateway, NATGateway
)
from diagrams.aws.compute import Fargate
from diagrams.aws.database import RDS, ElastiCache

# ---------------------------------------------------------
# 2) AWS - Network & Data (Deep Dive)   [unchanged, refined]
# ---------------------------------------------------------
with Diagram("AWS - Network & Data (Deep Dive)", filename="aws_network_and_data", direction="TB", show=False, node_attr=node_attr):
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
