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
from diagrams.aws.compute import ECR, EKS
from diagrams.aws.management import Cloudwatch

# GitOps
from diagrams.onprem.gitops import ArgoCD

# IaC
from diagrams.onprem.iac import Terraform

# Monitoring
from diagrams.aws.management import AmazonManagedGrafana

# ---- A. Fix Graphviz PATH for Windows (harmless on Linux/Mac) ----
graphviz_bin = r"C:\Program Files\Graphviz\bin"
if os.name == "nt" and os.path.isdir(graphviz_bin):
    os.environ["PATH"] = graphviz_bin + os.pathsep + os.environ.get("PATH", "")
    os.environ["GRAPHVIZ_DOT"] = os.path.join(graphviz_bin, "dot.exe")


# -----------------
# 3) CI/CD Pipeline
# -----------------
with Diagram("CI/CD Pipeline", filename="cicd_pipeline", direction="LR", show=False, node_attr=node_attr):
    dev = User("Developer")
    repo = Github("GitHub Repo\n(main + Helm charts)")
    ci = GithubActions("GitHub Actions\nWorkflow")

    with Cluster("CI"):
        tests = GithubActions("Run Tests")
        build = GithubActions("Build Docker Image")
        push = GithubActions("Push to ECR")

    with Cluster("CD"):
        deploy = ArgoCD("ArgoCD\nDeploy to Kubernetes")

    with Cluster("Infrastructure"):
        terraform = Terraform("Terraform\nProvision EKS & Infra")
        eks = EKS("EKS Cluster")
        registry = ECR("AWS ECR")
        grafana = AmazonManagedGrafana("Grafana\nMonitoring & Dashboards")

    dev >> Edge(label="git push") >> repo >> ci
    repo >> terraform
    ci >> tests >> build >> push >> deploy
    push >> registry
    terraform >> eks
    deploy >> eks >> grafana
