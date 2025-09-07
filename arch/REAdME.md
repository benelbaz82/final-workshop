## **Architectural Design Document: "Status-Page" Application on AWS EKS**

### **1. Introduction**

#### **1.1. Purpose**
This document describes the architecture for deploying and operating the Status-Page Django-based application on Amazon Web Services (AWS) using Elastic Kubernetes Service (EKS). The objective is to deliver a modern, secure, scalable, and highly available infrastructure.

#### **1.2. Scope**
The architecture spans all layers of the system, from networking and compute to data storage, security, CI/CD automation, and observability.

### **2. Architectural Goals and Principles**

#### **2.1. Goals**
* **High Availability:** Multi-AZ deployment of all core services, eliminating single points of failure.
* **Scalability:** Horizontal Pod Autoscaler (HPA) for workloads and Cluster Autoscaler for nodes.
* **Security:** Use of IAM Roles for Service Accounts (IRSA), AWS Secrets Manager, and TLS termination at CloudFront/ALB.
* **Automation:** Full CI/CD pipeline with GitHub Actions and Infrastructure-as-Code.
* **Observability:** Metrics, dashboards, and logs available in real-time for proactive monitoring.
  
#### **2.2. Guiding Principles**
* **Infrastructure as Code (IaC):** All infrastructure components are defined and managed through code (YAML files) to maintain consistency and enable easy recovery.
* **Immutable Infrastructure:** Independent deployments for Web, Worker, and Scheduler.
* **Microservice Separation:** Separating the application's different components (Web, Worker, Scheduler) into distinct containers to improve flexibility and scalability.
* **Managed Services:** Minimize operational overhead by leveraging AWS-managed services (RDS, ElastiCache, OpenSearch, Prometheus, Grafana).

### **3. System Architecture**


#### **3.1. High-Level Diagram**
* Users connect via Route 53 → CloudFront → ALB.
* ALB forwards requests to the Ingress Controller inside the EKS cluster.
* Ingress routes traffic to the Web Deployment pods.
* Web, Worker, and Scheduler deployments interact with RDS (PostgreSQL), ElastiCache (Redis), and Amazon OpenSearch Service.
* Secrets (DB, Redis, Django secret key) are securely fetched from AWS Secrets Manager and mounted into pods via the Secrets Store CSI Driver with IRSA permissions.
* Application and cluster metrics are collected in Amazon Managed Prometheus and visualized in Amazon Managed Grafana.

#### **3.2. Component Breakdown**

**3.2.1. AWS Infrastructure**
* **VPC (Virtual Private Cloud):** Spans multiple AZs with public subnets for ALB and private subnets for EKS nodes and databases.
* **EKS Cluster:**
    * **Control Plane:** Fully managed by AWS, distributed across multiple AZs for high availability.
    * **Node Groups:** EC2 worker nodes (multi-AZ), auto-scaled by the Cluster Autoscaler.

**3.2.2. Data Layer**
* **Amazon RDS (PostgreSQL, Multi-AZ):** Relational database backend with automatic failover.
* **Amazon ElastiCache (Redis, Multi-AZ):** For caching and task queues.
* **Amazon OpenSearch Service (Multi-AZ):** For log indexing, search, and analytics.

**3.2.3. Application Layer (Kubernetes)**
* **Ingress & Services:** TRoute traffic from ALB to the right deployments
* **Deployments:**
  * Web Deployment (frontend, auto-scaled with HPA).
  * RQ Worker Deployment (background tasks, 2 replicas).
  * Scheduler Deployment (periodic tasks, 1 replica).
* **Autoscaling:**
  * HPA scales pods based on resource usage.
  * Cluster Autoscaler adjusts node count.
* **Secrets Management:**
  * AWS Secrets Manager: Stores credentials and sensitive keys.
  * SecretProviderClass + CSI Driver: Mounts secrets directly into pods.
  * IRSA: Provides least-privilege IAM permissions to Kubernetes Service Accounts.

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
    * **Amazon Managed Prometheus:** To collect metrics from all cluster and application components.
    * **Amazon Managed Grafana:** To visualize the collected metrics in dashboards.
* **Logging:**
    * **OpenSearch:** for indexing and searching logs
    * **CloudWatch Logs:** for aggregation and retention
* **Alerting:** Grafana and CloudWatch provide real-time alerts based on defined thresholds.
