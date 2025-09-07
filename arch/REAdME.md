## **Architectural Design Document: "Status-Page" Application on AWS EKS**

### **1. Introduction**

#### **1.1. Purpose**
This document describes the comprehensive architecture for running, managing, and maintaining the "Status-Page" Django-based application in a production environment on Amazon Web Services (AWS). The objective is to establish a modern, secure, scalable, and highly available infrastructure using Amazon Elastic Kubernetes Service (EKS).

#### **1.2. Scope**
The architecture encompasses all required components, from the network infrastructure (VPC), through the compute layer (EKS), data layer (RDS, ElastiCache), security, CI/CD processes, and a complete monitoring and logging system.

### **2. Architectural Goals and Principles**

#### **2.1. Goals**
* **High Availability:** Ensure continuous application uptime by preventing single points of failure (SPOF) and distributing components across multiple Availability Zones (AZs).
* **Scalability:** The ability to automatically scale resources up and down based on user load.
* **Security:** Implement security at every layer of the system, from the network to the application level, adhering to the principle of least privilege.
* **Automation:** Full automation of the build, test, and deployment processes (CI/CD) to enable rapid and reliable development.
* **Observability:** The ability to monitor, collect logs, and receive real-time alerts to quickly identify and resolve issues.

#### **2.2. Guiding Principles**
* **Infrastructure as Code (IaC):** All infrastructure components are defined and managed through code (YAML files) to maintain consistency and enable easy recovery.
* **Immutable Infrastructure:** Containers are immutable units. Any change requires building and deploying a new version.
* **Decoupling:** Separating the application's different components (Web, Worker, Scheduler) into distinct containers to improve flexibility and scalability.
* **Managed Services:** Preferring the use of AWS managed services (such as RDS, ElastiCache, EKS Control Plane) to reduce the operational maintenance burden.

### **3. System Architecture**

#### **3.1. High-Level Diagram**
The application is deployed on an EKS cluster spanning three Availability Zones. User traffic enters through an Application Load Balancer (ALB), which routes requests to the application's web components. The web components communicate with a PostgreSQL database (RDS) and a Redis task queue (ElastiCache). The Worker and Scheduler components consume tasks from the Redis queue. All internal and external communication is secured and restricted.

#### **3.2. Component Breakdown**

**3.2.1. AWS Infrastructure**
* **VPC (Virtual Private Cloud):** An isolated virtual network spanning 3 AZs. It includes public subnets for network components (like the ALB) and private subnets for compute resources (EKS Nodes) and the data layer.
* **EKS Cluster:**
    * **Control Plane:** Fully managed by AWS, distributed across multiple AZs for high availability.
    * **Data Plane:** Comprised of EKS Managed Node Groups, running EC2 instances within the private subnets.

**3.2.2. Data Layer**
* **Database:** Amazon RDS for PostgreSQL service in a Multi-AZ configuration, ensuring automatic failover in case of an outage.
* **Cache & Queue:** Amazon ElastiCache for Redis service, used for both caching and as a message queue. It is also configured in a Multi-AZ setup.

**3.2.3. Application Layer (Kubernetes)**
* **Containerization:** The application is split into 3 separate Docker images (Web, RQ Worker, RQ Scheduler) using Multi-Stage Builds to optimize for size and security. The images are stored in Amazon ECR.
* **Deployments:** Each application component will have its own Kubernetes Deployment, allowing for version management, replication, and rolling updates.
* **Autoscaling:** A Horizontal Pod Autoscaler (HPA) will be used to automatically scale the number of web component pods based on CPU consumption.
* **Traffic Management:** The AWS Load Balancer Controller will be used to automatically create and manage an ALB via a Kubernetes Ingress object, enabling secure external exposure of the service.

### **4. Security Design**
* **IAM Roles for Service Accounts (IRSA):** Attaching dedicated IAM Roles with least-privilege permissions directly to the pods' Service Accounts. This eliminates the need to manage static access keys within the cluster.
* **Secrets Management:** All secrets (passwords, API keys) will be managed in AWS Secrets Manager. Secrets will be securely injected into pods using the Secrets Store CSI Driver.
* **Network Policies:** Kubernetes Network Policies will be used to define internal firewall rules within the cluster. Communication will only be allowed between pods that require it.
* **Security Groups:** Access to the database (RDS) and Redis (ElastiCache) will be restricted at the network level. Only the EKS Worker Nodes will have access.

### **5. CI/CD Pipeline**
* **Source Control:** GitHub.
* **Automation Server:** GitHub Actions.
* **Workflow:**
    1.  **Trigger:** A code push to the main branch.
    2.  **Build:** Build the 3 application Docker images and tag them with the commit hash.
    3.  **Push:** Push the new images to the private repository in Amazon ECR.
    4.  **Deploy:** Automatically update the relevant Kubernetes Deployment files with the new image tags and apply the changes. This process initiates a zero-downtime rolling update.

### **6. Observability**
* **Monitoring & Alerting:**
    * **Prometheus:** To collect metrics from all cluster and application components.
    * **Grafana:** To visualize the collected metrics in dashboards.
* **Logging:**
    * **Fluent Bit:** A DaemonSet that will run on every node in the cluster to collect logs from all containers.
    * **Amazon CloudWatch:** Logs will be sent to CloudWatch Logs for centralized aggregation, analysis, and long-term storage.