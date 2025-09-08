from diagrams import Diagram, Cluster
from diagrams.aws.compute import EKS
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.network import VPC, InternetGateway, NATGateway, ALB, Nacl
from diagrams.aws.general import User, GenericFirewall
import os
import sys

# Add the parent directory 'arch' to the Python path to import settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import node_attr, cluster_attr

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

    with Cluster("AWS Region", graph_attr=cluster_attr):
        igw = InternetGateway("IGW")
        alb = ALB("ALB")
        alb_sg = GenericFirewall("ALB Security Group")
        
        with Cluster("VPC (10.0.0.0/16)", graph_attr=cluster_attr):

            with Cluster("Availability Zone 1 (us-east-1a)", graph_attr=cluster_attr):
                with Cluster("Public Subnet 1 (10.0.1.0/24)", graph_attr=cluster_attr):
                    nat1 = NATGateway("NAT GW 1")
                    nacl_public1 = Nacl("Nacl")

                with Cluster("Private App Subnet 1 (10.0.11.0/24)", graph_attr=cluster_attr):
                    eks_nodes1 = EKS("EKS Worker Nodes")
                    eks_sg1 = GenericFirewall("EKS Security Group")
                    nacl_app1 = Nacl("Nacl")

                with Cluster("Private Data Subnet 1 (10.0.21.0/24)", graph_attr=cluster_attr):
                    db1 = RDS("RDS Instance 1")
                    cache1 = ElastiCache("Cache Instance 1")
                    db_sg1 = GenericFirewall("DB Security Group")
                    nacl_data1 = Nacl("Nacl")

            with Cluster("Availability Zone 2 (us-east-1b)", graph_attr=cluster_attr):
                with Cluster("Public Subnet 2 (10.0.2.0/24)", graph_attr=cluster_attr):
                    nat2 = NATGateway("NAT GW 2")
                    nacl_public2 = Nacl("Nacl")

                with Cluster("Private App Subnet 2 (10.0.12.0/24)", graph_attr=cluster_attr):
                    eks_nodes2 = EKS("EKS Worker Nodes")
                    eks_sg2 = GenericFirewall("EKS Security Group")
                    nacl_app2 = Nacl("Nacl")

                with Cluster("Private Data Subnet 2 (10.0.22.0/24)", graph_attr=cluster_attr):
                    db2 = RDS("RDS Instance 2")
                    cache2 = ElastiCache("Cache Instance 2")
                    db_sg2 = GenericFirewall("DB Security Group")
                    nacl_data2 = Nacl("Nacl")

            with Cluster("Availability Zone 3 (us-east-1c)", graph_attr=cluster_attr):
                with Cluster("Public Subnet 3 (10.0.3.0/24)", graph_attr=cluster_attr):
                    nat3 = NATGateway("NAT GW 3")
                    nacl_public3 = Nacl("Nacl")

                with Cluster("Private App Subnet 3 (10.0.13.0/24)", graph_attr=cluster_attr):
                    eks_nodes3 = EKS("EKS Worker Nodes")
                    eks_sg3 = GenericFirewall("EKS Security Group")
                    nacl_app3 = Nacl("Nacl")

                with Cluster("Private Data Subnet 3 (10.0.23.0/24)", graph_attr=cluster_attr):
                    db3 = RDS("RDS Instance 3")
                    cache3 = ElastiCache("Cache Instance 3")
                    db_sg3 = GenericFirewall("DB Security Group")
                    nacl_data3 = Nacl("Nacl")

            # --- Traffic Flow ---
            # User to ALB through IGW
            user >> igw >> alb

            # ALB Security Group controls inbound traffic
            alb >> alb_sg

            # ALB to EKS Nodes (through Security Groups and NACLs)
            alb_sg >> nacl_app1 >> eks_sg1 >> eks_nodes1
            alb_sg >> nacl_app2 >> eks_sg2 >> eks_nodes2
            alb_sg >> nacl_app3 >> eks_sg3 >> eks_nodes3

            # EKS to Data Layer (through Security Groups and NACLs)
            eks_nodes1 >> eks_sg1 >> nacl_data1 >> db_sg1 >> [db1, cache1]
            eks_nodes2 >> eks_sg2 >> nacl_data2 >> db_sg2 >> [db2, cache2]
            eks_nodes3 >> eks_sg3 >> nacl_data3 >> db_sg3 >> [db3, cache3]

            # EKS to Internet via NAT (Outbound through NACLs)
            eks_nodes1 >> nacl_public1 >> nat1
            eks_nodes2 >> nacl_public2 >> nat2
            eks_nodes3 >> nacl_public3 >> nat3

