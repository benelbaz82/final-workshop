from diagrams import Diagram, Cluster
from diagrams.aws.compute import EKS
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.network import VPC, InternetGateway, NATGateway, ALB
from diagrams.aws.general import User
import os
import sys

# Add the parent directory 'arch' to the Python path to import settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import node_attr

# ---- A. Fix Graphviz PATH for Windows (harmless on Linux/Mac) ----
graphviz_bin = r"C:\Program Files\Graphviz\bin"
if os.name == "nt" and os.path.isdir(graphviz_bin):
    os.environ["PATH"] = graphviz_bin + os.pathsep + os.environ.get("PATH", "")
    os.environ["GRAPHVIZ_DOT"] = os.path.join(graphviz_bin, "dot.exe")

# Set the output filename for the diagram
script_dir = os.path.dirname(os.path.abspath(__file__))
output_filename = os.path.join(script_dir, "aws_network_and_data")

with Diagram("AWS VPC Network Architecture", show=False, direction="TB", filename=output_filename, node_attr=node_attr):
    user = User("Internet User")

    with Cluster("AWS Region"):
        with Cluster("VPC (10.0.0.0/16)"):
            igw = InternetGateway("IGW")
            alb = ALB("ALB")

            with Cluster("Availability Zone 1 (us-east-1a)"):
                with Cluster("Public Subnet 1 (10.0.1.0/24)"):
                    nat1 = NATGateway("NAT GW 1")

                with Cluster("Private App Subnet 1 (10.0.11.0/24)"):
                    eks_nodes1 = EKS("EKS Worker Nodes")

                with Cluster("Private Data Subnet 1 (10.0.21.0/24)"):
                    db1 = RDS("RDS Instance 1")
                    cache1 = ElastiCache("Cache Instance 1")

            with Cluster("Availability Zone 2 (us-east-1b)"):
                with Cluster("Public Subnet 2 (10.0.2.0/24)"):
                    nat2 = NATGateway("NAT GW 2")

                with Cluster("Private App Subnet 2 (10.0.12.0/24)"):
                    eks_nodes2 = EKS("EKS Worker Nodes")

                with Cluster("Private Data Subnet 2 (10.0.22.0/24)"):
                    db2 = RDS("RDS Instance 2")
                    cache2 = ElastiCache("Cache Instance 2")

            with Cluster("Availability Zone 3 (us-east-1c)"):
                with Cluster("Public Subnet 3 (10.0.3.0/24)"):
                    nat3 = NATGateway("NAT GW 3")

                with Cluster("Private App Subnet 3 (10.0.13.0/24)"):
                    eks_nodes3 = EKS("EKS Worker Nodes")

                with Cluster("Private Data Subnet 3 (10.0.23.0/24)"):
                    db3 = RDS("RDS Instance 3")
                    cache3 = ElastiCache("Cache Instance 3")

            # --- Traffic Flow ---
            # User to ALB
            user >> igw >> alb

            # ALB to EKS Nodes (Represents ALB SG allowing traffic)
            alb >> eks_nodes1
            alb >> eks_nodes2
            alb >> eks_nodes3

            # EKS to Data Layer (Represents EKS SG to Data SG)
            eks_nodes1 >> db1
            eks_nodes1 >> cache1
            eks_nodes2 >> db2
            eks_nodes2 >> cache2
            eks_nodes3 >> db3
            eks_nodes3 >> cache3

            # EKS to Internet via NAT (Outbound)
            eks_nodes1 >> nat1
            eks_nodes2 >> nat2
            eks_nodes3 >> nat3

