# -*- coding: utf-8 -*-
# main.py
# Generate architecture diagrams for the Final Workshop:
# 4) Single VM Alternative (Dev/Test)

from diagrams import Diagram, Cluster, Edge
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from settings import node_attr

# On-prem / general
from diagrams.onprem.client import User
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.network import Nginx

# --------------------------------------
# 4) Single VM Alternative (Dev/Test)
# --------------------------------------
with Diagram("Single VM Alternative (Dev/Test)", filename="single_vm_alternative", direction="TB", show=False, node_attr=node_attr):
    user = User("End User")
    with Cluster("Single Linux Server\n(CentOS/Ubuntu)"):
        http = Nginx("Nginx")  # or Apache()
        gunicorn = Server("Gunicorn + Django")
        db = PostgreSQL("PostgreSQL 10+ :5432")
        cache = Redis("Redis 4+ :6379")

    user >> Edge(label="HTTPS 443 / HTTP 8000") >> http >> Edge(label="proxy → 8000") >> gunicorn
    gunicorn >> db
    gunicorn >> cache
