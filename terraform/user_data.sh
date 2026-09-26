#!/usr/bin/env bash
# RakshakGIS EC2 Cloud-Init Bootstrap Script
# Target OS: Ubuntu 22.04 / 24.04 LTS

set -euo pipefail
exec > >(tee -a /var/log/user_data.log) 2>&1

echo "===================================================="
echo "RakshakGIS Server Bootstrap Started: $(date -u)"
echo "===================================================="

export DEBIAN_FRONTEND=noninteractive

# 1. Configure 2 GiB Swapfile (Protects against OOM during PostGIS/Next.js execution)
if [ ! -f /swapfile ]; then
    echo "Configuring 2 GiB swapfile..."
    fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "Swap configured successfully."
else
    echo "Swapfile already exists. Skipping."
fi

# 2. Update System Packages
echo "Updating apt package index..."
apt-get update -y
apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw \
    jq \
    htop

# 3. Install Docker Engine and Docker Compose v2 Plugin
echo "Setting up Docker official repository..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y --no-install-recommends \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

# 4. Enable and Start Docker Service
systemctl enable docker
systemctl start docker

# Add ubuntu user to docker group
if id -u ubuntu >/dev/null 2>&1; then
    usermod -aG docker ubuntu
    echo "Added 'ubuntu' user to docker group."
fi

# 5. Create Application Directory
mkdir -p /opt/rakshakgis
if id -u ubuntu >/dev/null 2>&1; then
    chown -R ubuntu:ubuntu /opt/rakshakgis
fi

echo "===================================================="
echo "RakshakGIS Server Bootstrap Completed: $(date -u)"
echo "Docker version: $(docker --version)"
echo "Docker Compose version: $(docker compose version)"
echo "===================================================="
