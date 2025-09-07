# -*- coding: utf-8 -*-
# main.py
# Generate architecture diagrams for the Final Workshop:
# 3) CI/CD Pipeline

from diagrams import Diagram, Cluster, Edge
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from settings import node_attr

# On-prem / general
from diagrams.onprem.client import User
from diagrams.onprem.vcs import Github
from diagrams.onprem.ci import GithubActions

# AWS common
from diagrams.aws.compute import ECS, ECR
from diagrams.aws.management import Cloudwatch

# -----------------
# 3) CI/CD Pipeline
# -----------------
with Diagram("CI/CD Pipeline", filename="cicd_pipeline", direction="LR", show=False, node_attr=node_attr):
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
