# RakshakGIS — AWS Terraform Infrastructure

This directory provides Terraform configurations to provision a secure, isolated, single-node cloud environment on Amazon Web Services (AWS) for **RakshakGIS**.

---

## 1. Architecture Overview

```
                      AWS Cloud (Region: e.g. ap-south-1)
  +--------------------------------------------------------------------+
  | Dedicated VPC (10.0.0.0/16)                                        |
  |                                                                    |
  |   +------------------------------------------------------------+   |
  |   | Public Subnet (10.0.1.0/24)                                |   |
  |   |                                                            |   |
  |   |   Security Group:                                          |   |
  |   |   - Port 22: SSH (Restricted to admin_ssh_cidr)            |   |
  |   |   - Port 80/443: HTTP/HTTPS (Public web access)            |   |
  |   |   - Port 3000/8000: Direct App Ports (Closed by default;   |   |
  |   |     restricted to admin CIDR if enable_direct_app_ports)   |   |
  |   |   - Port 5432: PostgreSQL/PostGIS (STRICTLY PROHIBITED)    |   |
  |   |                                                            |   |
  |   |   +----------------------------------------------------+   |   |
  |   |   | EC2 Instance (t3.small recommended, Ubuntu 22.04)  |   |   |
  |   |   | Attached Elastic IP (Static Public IPv4)           |   |   |
  |   |   |                                                    |   |   |
  |   |   | User Data Cloud-Init:                              |   |   |
  |   |   | - 2 GiB Swapfile (/swapfile)                       |   |   |
  |   |   | - Docker Engine 26+ & Docker Compose v2 Plugin     |   |   |
  |   |   | - App directory: /opt/rakshakgis                   |   |   |
  |   |   +----------------------------------------------------+   |   |
  |   +------------------------------------------------------------+   |
  |                                 |                                  |
  |                      Internet Gateway (IGW)                        |
  +--------------------------------------------------------------------+
                                    |
                           [ Public Internet ]
```

### Security Posture & Guarantees
1. **Database Isolation:** PostgreSQL port 5432 is **never** opened to the public Internet in the security group. Database queries remain strictly internal to the Docker bridge network on the host.
2. **Reverse Proxy Architecture:** Public web traffic enters exclusively via HTTP (port 80) and HTTPS (port 443). FastAPI port 8000 and Next.js direct port 3000 are closed to the public Internet (`0.0.0.0/0`), eliminating unnecessary attack surface.
3. **Access Control:** SSH (port 22) is restricted to operator IPs or corporate VPNs via `admin_ssh_cidr`.
4. **Automated Swap Allocation:** To prevent kernel Out-Of-Memory (OOM) terminations during memory-intensive PostGIS spatial indexing or Next.js compilation, the cloud-init bootstrap script configures a dedicated **2 GiB swapfile** on the encrypted root volume.

---

## 2. Prerequisites

1. **Terraform CLI:** Version `1.5.0` or higher installed.
2. **AWS Credentials:** Configured via environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`), AWS CLI (`aws configure`), or IAM instance profiles.
3. **AWS EC2 Key Pair:** An existing key pair in the target AWS region if SSH access via key is desired.

---

## 3. Quickstart & Deployment Runbook

### Step 1: Configure Variables
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```
Edit `terraform.tfvars` with your settings:
```hcl
aws_region     = "ap-south-1"      # Asia Pacific (Mumbai)
environment    = "prod"
instance_type  = "t3.small"        # 2 vCPU, 2 GiB RAM
key_name       = "your-key-name"   # Key pair for SSH
admin_ssh_cidr = ["YOUR_IP/32"]    # Restrict SSH access
```

### Step 2: Initialize & Validate
```bash
terraform init
terraform validate
```

### Step 3: Review Plan & Apply
```bash
terraform plan -out=tfplan
terraform apply tfplan
```

### Step 4: Access Outputs
Terraform will display connection information upon completion:
```
Outputs:
frontend_url          = "http://13.232.xxx.xxx"
backend_api_url       = "http://13.232.xxx.xxx/api/v1"
backend_health_url    = "http://13.232.xxx.xxx/health"
public_ip             = "13.232.xxx.xxx"
ssh_connection_string = "ssh -i <your-key.pem> ubuntu@13.232.xxx.xxx"
```

---

## 4. Bootstrapping RakshakGIS on the Instance

Once the instance is running (allow 2-3 minutes for cloud-init bootstrap to finish installing Docker):

1. **Connect via SSH:**
   ```bash
   ssh -i ~/.ssh/your-key.pem ubuntu@<PUBLIC_IP>
   ```

2. **Verify Docker and Compose Installation:**
   ```bash
   docker --version
   docker compose version
   cat /var/log/user_data.log
   ```

3. **Deploy the Production Stack:**
   ```bash
   cd /opt/rakshakgis
   git clone https://github.com/OjaswiJoshi13/rakshakgis.git .

   # Set mandatory production secrets
   export POSTGRES_PASSWORD="<strong-database-password>"
   export JWT_SECRET="<64-char-hex-jwt-secret>"

   # Launch production containers
   docker compose -f docker-compose.prod.yml up -d
   ```

4. **Verify Container Health:**
   ```bash
   docker compose -f docker-compose.prod.yml ps
   curl http://127.0.0.1:8000/health
   curl http://127.0.0.1:3000/health
   ```

---

## 5. Teardown & Cleanup

To destroy all provisioned AWS cloud resources:
```bash
terraform destroy
```
*(Confirm with `yes` when prompted).*
