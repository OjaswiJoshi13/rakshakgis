variable "aws_region" {
  description = "The AWS region where resources will be provisioned."
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Deployment environment name (e.g., prod, staging, dev)."
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name prefix used for resource naming and tagging."
  type        = string
  default     = "rakshakgis"
}

variable "vpc_cidr" {
  description = "CIDR block for the dedicated RakshakGIS VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet hosting the application EC2 instance."
  type        = string
  default     = "10.0.1.0/24"
}

variable "instance_type" {
  description = "EC2 instance type. Recommended: t3.small (2 vCPU, 2 GiB RAM) or t3.medium (2 vCPU, 4 GiB RAM). CAVEAT: t2.micro (1 GiB RAM) may fail with OOM errors during PostGIS operations and Next.js execution unless 2GB swap is enabled."
  type        = string
  default     = "t3.small"
}

variable "key_name" {
  description = "Optional name of an existing EC2 Key Pair for SSH access. If omitted, SSH password/key access is not pre-configured (AWS SSM Session Manager recommended)."
  type        = string
  default     = ""
}

variable "admin_ssh_cidr" {
  description = "List of IPv4 CIDR blocks permitted to establish SSH connections on port 22. WARNING: In production, restrict this to your specific operator IP/VPN."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "root_volume_size" {
  description = "Root EBS storage volume size in GiB. Minimum 20 GiB recommended for Docker images and PostGIS data."
  type        = number
  default     = 30
}

variable "root_volume_type" {
  description = "Root EBS storage volume type."
  type        = string
  default     = "gp3"
}

variable "allocate_elastic_ip" {
  description = "Whether to allocate and attach an AWS Elastic IP for static public IP addressing."
  type        = bool
  default     = true
}
