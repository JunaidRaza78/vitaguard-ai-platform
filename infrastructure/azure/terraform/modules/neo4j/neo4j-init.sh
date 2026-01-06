#!/bin/bash
# Neo4j Installation and Configuration Script for Azure VM

set -e

# Variables
NEO4J_PASSWORD="${neo4j_password}"
ENVIRONMENT="${environment}"
NEO4J_VERSION="5.15.0"

echo "Starting Neo4j installation..."

# Update system
apt-get update
apt-get upgrade -y

# Install Java 17
apt-get install -y openjdk-17-jdk wget gnupg

# Add Neo4j repository
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | apt-key add -
echo 'deb https://debian.neo4j.com stable latest' > /etc/apt/sources.list.d/neo4j.list

# Install Neo4j
apt-get update
apt-get install -y neo4j=$NEO4J_VERSION

# Format and mount data disk
echo "Configuring data disk..."
mkfs.ext4 /dev/sdc
mkdir -p /mnt/neo4j-data
mount /dev/sdc /mnt/neo4j-data
echo '/dev/sdc /mnt/neo4j-data ext4 defaults,nofail 0 2' >> /etc/fstab

# Create Neo4j directories on data disk
mkdir -p /mnt/neo4j-data/data
mkdir -p /mnt/neo4j-data/logs
mkdir -p /mnt/neo4j-data/import
mkdir -p /mnt/neo4j-data/plugins
chown -R neo4j:neo4j /mnt/neo4j-data

# Configure Neo4j
cat > /etc/neo4j/neo4j.conf <<EOF
# Network settings
server.default_listen_address=0.0.0.0
server.bolt.enabled=true
server.bolt.listen_address=:7687
server.http.enabled=true
server.http.listen_address=:7474
server.https.enabled=false

# Database location
server.directories.data=/mnt/neo4j-data/data
server.directories.logs=/mnt/neo4j-data/logs
server.directories.import=/mnt/neo4j-data/import
server.directories.plugins=/mnt/neo4j-data/plugins

# Memory settings
server.memory.heap.initial_size=2g
server.memory.heap.max_size=4g
server.memory.pagecache.size=2g

# Security
dbms.security.auth_enabled=true

# Performance
dbms.checkpoint.iops.limit=1000
db.tx_log.rotation.retention_policy=1 days

# Logging
server.logs.gc.enabled=true
server.logs.debug.level=INFO
EOF

# Set initial password
neo4j-admin dbms set-initial-password "$NEO4J_PASSWORD"

# Enable and start Neo4j
systemctl enable neo4j
systemctl start neo4j

# Wait for Neo4j to start
echo "Waiting for Neo4j to start..."
sleep 30

# Verify Neo4j is running
systemctl status neo4j

echo "Neo4j installation completed!"
echo "Bolt: bolt://$(hostname -I | awk '{print $1}'):7687"
echo "HTTP: http://$(hostname -I | awk '{print $1}'):7474"
