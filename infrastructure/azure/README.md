# Azure Infrastructure & CI/CD Documentation

Comprehensive guide for deploying the Agentic AI Family Health Manager on Microsoft Azure.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Quick Start](#quick-start)
5. [CI/CD Pipelines](#cicd-pipelines)
6. [Terraform Infrastructure](#terraform-infrastructure)
7. [Manual Deployment](#manual-deployment)
8. [Configuration](#configuration)
9. [Security](#security)
10. [Monitoring](#monitoring)
11. [Cost Optimization](#cost-optimization)
12. [Troubleshooting](#troubleshooting)

---

## Overview

This infrastructure deploys a production-ready, HIPAA-compliant healthcare management system on Azure with:

- **App Service** - Containerized Python application
- **Azure Container Registry** - Private Docker registry
- **PostgreSQL Flexible Server** - Transactional database
- **Cosmos DB (MongoDB API)** - Document storage
- **Neo4j VM** - Knowledge graph database
- **Redis Cache** - Session and caching layer
- **Azure Storage** - Medical document storage
- **Key Vault** - Secrets management
- **Application Insights** - Monitoring and logging
- **Virtual Network** - Network isolation

### Environments

- **Development** (`dev`) - Feature testing, auto-deploy from `develop` branch
- **Staging** (`staging`) - Pre-production testing, auto-deploy from `release/*` branches
- **Production** (`prod`) - Live environment, auto-deploy from `main` branch with blue-green deployment

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Azure Front Door (Optional)                 │
│                    WAF + CDN + Global Load Balancing             │
└─────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                         Azure App Service                        │
│                    Linux Container (Docker)                      │
│               VNet Integration + Managed Identity                │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
         ┌──────────▼──────────┐   ┌─────────▼──────────┐
         │   Azure Key Vault   │   │  Application       │
         │   (Secrets)         │   │  Insights          │
         └─────────────────────┘   └────────────────────┘
                                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Virtual Network (VNet)                      │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐            │
│  │ PostgreSQL  │  │  Cosmos DB  │  │  Neo4j VM    │            │
│  │ Flexible    │  │  (MongoDB)  │  │              │            │
│  └─────────────┘  └─────────────┘  └──────────────┘            │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐                               │
│  │ Redis Cache │  │   Storage   │                               │
│  │             │  │  (Blob)     │                               │
│  └─────────────┘  └─────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Required Tools

```bash
# Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
az --version

# Terraform
wget https://releases.hashicorp.com/terraform/1.6.6/terraform_1.6.6_linux_amd64.zip
unzip terraform_1.6.6_linux_amd64.zip
sudo mv terraform /usr/local/bin/
terraform --version

# Docker
sudo apt-get update
sudo apt-get install docker.io docker-compose
docker --version

# Git
sudo apt-get install git
```

### Azure Subscription

1. **Create Azure Subscription** (if not already exists)
2. **Create Service Principal** for CI/CD:

```bash
# Login to Azure
az login

# Create service principal
az ad sp create-for-rbac \
  --name "sp-health-manager-cicd" \
  --role Contributor \
  --scopes /subscriptions/{subscription-id} \
  --sdk-auth

# Save output for GitHub Secrets / Azure DevOps
```

3. **Set Required Permissions**:
   - Contributor on Resource Group
   - Key Vault Administrator
   - Storage Blob Data Contributor

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/agentic-ai-family-health-manager.git
cd agentic-ai-family-health-manager
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your values
vim .env
```

### 3. Deploy Infrastructure

```bash
cd infrastructure/azure/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="environment=dev" -out=tfplan

# Apply deployment
terraform apply tfplan
```

### 4. Configure Secrets

```bash
# Set OpenAI API Key
az keyvault secret set \
  --vault-name kv-health-dev \
  --name openai-api-key \
  --value "your-openai-key"

# Set Anthropic API Key
az keyvault secret set \
  --vault-name kv-health-dev \
  --name anthropic-api-key \
  --value "your-anthropic-key"
```

### 5. Deploy Application

```bash
# Build and push Docker image
az acr build \
  --registry crhealthmanagerdev \
  --image health-manager:latest \
  --file Backend/Dockerfile .

# Restart App Service
az webapp restart \
  --resource-group rg-health-manager-dev \
  --name app-health-manager-dev
```

---

## CI/CD Pipelines

### GitHub Actions

The project uses GitHub Actions for automated CI/CD. Workflows are triggered based on branch:

- **`develop` branch** → Deploy to Development
- **`release/*` branches** → Deploy to Staging
- **`main` branch** → Deploy to Production (with blue-green)

#### Setup GitHub Secrets

Navigate to **Settings → Secrets and variables → Actions** and add:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `AZURE_CREDENTIALS_DEV` | Service principal JSON for dev | `{"clientId":"..."}` |
| `AZURE_CREDENTIALS_STAGING` | Service principal JSON for staging | `{"clientId":"..."}` |
| `AZURE_CREDENTIALS_PROD` | Service principal JSON for prod | `{"clientId":"..."}` |
| `ACR_USERNAME` | Container registry username | `crhealthmanager` |
| `ACR_PASSWORD` | Container registry password | From Azure Portal |

#### Workflow Stages

1. **Build and Test**
   - Code quality checks (Black, Flake8, MyPy)
   - Unit tests with coverage
   - Docker image build
   - Security scan with Trivy

2. **Deploy Infrastructure**
   - Terraform apply
   - Database provisioning

3. **Deploy Application**
   - Push to Azure Container Registry
   - Deploy to App Service
   - Run database migrations

4. **Health Checks**
   - Smoke tests
   - Application health verification

### Azure DevOps

If using Azure DevOps instead:

1. **Import Pipeline**
   ```bash
   # In Azure DevOps
   Pipelines → New Pipeline → Existing YAML → Select .azure/pipelines/azure-pipelines.yml
   ```

2. **Configure Service Connection**
   - Project Settings → Service connections
   - New service connection → Azure Resource Manager
   - Use the service principal created earlier

3. **Configure Variables**
   - Pipelines → Library → Variable groups
   - Create groups for dev, staging, prod
   - Add Key Vault secrets

---

## Terraform Infrastructure

### Structure

```
infrastructure/azure/terraform/
├── main.tf              # Main infrastructure
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── modules/
│   ├── postgresql/      # PostgreSQL module
│   ├── mongodb/         # Cosmos DB module
│   └── neo4j/           # Neo4j VM module
```

### Key Resources

#### App Service Configuration

```hcl
# Scaling
- Dev: P1v3 (2 vCPU, 8GB RAM)
- Staging: P2v3 (4 vCPU, 16GB RAM)
- Prod: P3v3 (8 vCPU, 32GB RAM) with auto-scale

# Features
- VNet integration
- Managed identity
- Always On (staging/prod)
- Health check monitoring
- Blue-green deployment slot (prod)
```

#### Database Sizing

| Resource | Dev | Staging | Production |
|----------|-----|---------|------------|
| PostgreSQL | GP_Standard_D2s_v3 | GP_Standard_D2s_v3 | GP_Standard_D4s_v3 (HA) |
| Cosmos DB | 400 RU/s | 1000 RU/s | 4000 RU/s (Multi-region) |
| Neo4j VM | Standard_D2s_v3 | Standard_D2s_v3 | Standard_D4s_v3 |
| Redis | Standard (1GB) | Standard (2.5GB) | Premium (6GB) |

### Terraform Commands

```bash
# Initialize
terraform init \
  -backend-config="resource_group_name=rg-health-tfstate" \
  -backend-config="storage_account_name=sthealthtfstate" \
  -backend-config="container_name=tfstate" \
  -backend-config="key=dev.terraform.tfstate"

# Plan
terraform plan -var="environment=dev" -var-file="dev.tfvars" -out=tfplan

# Apply
terraform apply tfplan

# Destroy (careful!)
terraform destroy -var="environment=dev" -var-file="dev.tfvars"

# Show outputs
terraform output

# Import existing resource
terraform import azurerm_resource_group.main /subscriptions/{sub-id}/resourceGroups/rg-name
```

### Environment-Specific Variables

Create `{env}.tfvars` files:

```hcl
# dev.tfvars
environment          = "dev"
location            = "eastus"
app_service_sku     = "P1v3"
postgres_storage_mb = 32768
redis_capacity      = 1
```

---

## Manual Deployment

### Deploy Without CI/CD

1. **Create Resource Group**
   ```bash
   az group create \
     --name rg-health-manager-dev \
     --location eastus
   ```

2. **Deploy with Terraform**
   ```bash
   cd infrastructure/azure/terraform
   terraform init
   terraform apply -var="environment=dev"
   ```

3. **Build Docker Image**
   ```bash
   docker build -t health-manager:latest -f Backend/Dockerfile .
   ```

4. **Push to ACR**
   ```bash
   az acr login --name crhealthmanagerdev
   docker tag health-manager:latest crhealthmanagerdev.azurecr.io/health-manager:latest
   docker push crhealthmanagerdev.azurecr.io/health-manager:latest
   ```

5. **Update App Service**
   ```bash
   az webapp config container set \
     --resource-group rg-health-manager-dev \
     --name app-health-manager-dev \
     --docker-custom-image-name crhealthmanagerdev.azurecr.io/health-manager:latest
   ```

---

## Configuration

### Environment Variables

All secrets are stored in **Azure Key Vault** and referenced via App Settings:

```bash
@Microsoft.KeyVault(SecretUri=https://kv-health-dev.vault.azure.net/secrets/postgres-password/)
```

### App Settings Management

```bash
# List current settings
az webapp config appsettings list \
  --resource-group rg-health-manager-dev \
  --name app-health-manager-dev

# Update setting
az webapp config appsettings set \
  --resource-group rg-health-manager-dev \
  --name app-health-manager-dev \
  --settings ENVIRONMENT=production

# Remove setting
az webapp config appsettings delete \
  --resource-group rg-health-manager-dev \
  --name app-health-manager-dev \
  --setting-names DEBUG
```

### Scaling Configuration

```bash
# Manual scale
az appservice plan update \
  --resource-group rg-health-manager-prod \
  --name asp-health-manager-prod \
  --number-of-workers 5

# Auto-scale rule
az monitor autoscale create \
  --resource-group rg-health-manager-prod \
  --resource asp-health-manager-prod \
  --resource-type Microsoft.Web/serverfarms \
  --name autoscale-health-prod \
  --min-count 2 \
  --max-count 10 \
  --count 2

# Scale based on CPU
az monitor autoscale rule create \
  --resource-group rg-health-manager-prod \
  --autoscale-name autoscale-health-prod \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 2
```

---

## Security

### Network Security

```hcl
# VNet Integration - App Service connects via private network
# Private Endpoints - Databases accessible only within VNet
# NSG Rules - Firewall rules for Neo4j VM
# Service Endpoints - Secure connectivity for Azure services
```

### Identity & Access

```bash
# Managed Identity - App Service uses system-assigned identity
# Key Vault Access Policies - Identity has Get/List on secrets
# RBAC - Least privilege principle

# Grant Key Vault access
az keyvault set-policy \
  --name kv-health-prod \
  --object-id <app-service-identity-id> \
  --secret-permissions get list
```

### Data Encryption

- **At Rest**: All storage encrypted with Azure-managed keys
- **In Transit**: TLS 1.2+ enforced on all services
- **Application**: Sensitive data encrypted before storage

### Compliance

- HIPAA compliance enabled on all applicable services
- Audit logging enabled
- Data residency configured
- Business Associate Agreement (BAA) with Microsoft

---

## Monitoring

### Application Insights

```bash
# View logs
az monitor app-insights query \
  --app appi-health-manager-prod \
  --analytics-query "traces | where timestamp > ago(1h)"

# Check failures
az monitor app-insights query \
  --app appi-health-manager-prod \
  --analytics-query "requests | where success == false | top 10 by timestamp desc"
```

### Key Metrics

- **Response Time**: Target p95 < 200ms
- **Availability**: Target 99.9%
- **Error Rate**: Target < 0.1%
- **Database Connections**: Monitor pool utilization
- **Memory Usage**: Monitor for leaks
- **CPU Usage**: Auto-scale trigger at 70%

### Alerts

```bash
# Create alert for high error rate
az monitor metrics alert create \
  --name alert-high-error-rate \
  --resource-group rg-health-manager-prod \
  --scopes /subscriptions/{sub-id}/resourceGroups/rg-health-manager-prod/providers/Microsoft.Web/sites/app-health-manager-prod \
  --condition "avg exceptions/requests > 0.05" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action email ops@example.com
```

---

## Cost Optimization

### Monthly Cost Estimates

| Environment | Estimated Cost |
|-------------|----------------|
| Development | $300-500/month |
| Staging | $500-800/month |
| Production | $1,500-2,500/month |

### Cost Breakdown (Production)

- App Service (P3v3): $400/month
- PostgreSQL (HA): $350/month
- Cosmos DB (4000 RU/s): $470/month
- Neo4j VM (D4s_v3): $200/month
- Redis Premium: $180/month
- Storage: $50/month
- Monitoring: $100/month
- Networking: $150/month

### Optimization Tips

1. **Use Reserved Instances** - Save up to 72% on VMs
2. **Auto-shutdown Dev/Staging** - During non-business hours
3. **Use Spot VMs** - For Neo4j in dev/staging
4. **Optimize Cosmos DB** - Use autoscale, set appropriate RU/s
5. **Lifecycle Policies** - Auto-delete old blob data
6. **Review App Insights** - sampling for high-volume logs

```bash
# Enable auto-shutdown for Dev VM
az vm auto-shutdown \
  --resource-group rg-health-manager-dev \
  --name vm-neo4j-dev \
  --time 1900 \
  --timezone "Eastern Standard Time"
```

---

## Troubleshooting

### Common Issues

#### 1. App Service Not Starting

```bash
# Check logs
az webapp log tail \
  --resource-group rg-health-manager-dev \
  --name app-health-manager-dev

# Check container logs
az webapp log download \
  --resource-group rg-health-manager-dev \
  --name app-health-manager-dev \
  --log-file app-logs.zip
```

#### 2. Database Connection Issues

```bash
# Test PostgreSQL connectivity
az postgres flexible-server connect \
  --name psql-health-manager-dev \
  --admin-user pgadmin

# Check Neo4j VM
az vm run-command invoke \
  --resource-group rg-health-manager-dev \
  --name vm-neo4j-dev \
  --command-id RunShellScript \
  --scripts "systemctl status neo4j"
```

#### 3. High Memory Usage

```bash
# Increase App Service SKU
az appservice plan update \
  --resource-group rg-health-manager-prod \
  --name asp-health-manager-prod \
  --sku P3v3

# Or add more workers
az appservice plan update \
  --resource-group rg-health-manager-prod \
  --name asp-health-manager-prod \
  --number-of-workers 4
```

#### 4. Key Vault Access Denied

```bash
# Check access policy
az keyvault show \
  --name kv-health-prod \
  --query "properties.accessPolicies"

# Add access policy
az keyvault set-policy \
  --name kv-health-prod \
  --object-id <managed-identity-id> \
  --secret-permissions get list
```

### Debug Commands

```bash
# SSH into App Service container
az webapp ssh \
  --resource-group rg-health-manager-dev \
  --name app-health-manager-dev

# Check environment variables
az webapp config appsettings list \
  --resource-group rg-health-manager-dev \
  --name app-health-manager-dev \
  --output table

# Restart App Service
az webapp restart \
  --resource-group rg-health-manager-dev \
  --name app-health-manager-dev

# Check deployment status
az webapp deployment list-publishing-profiles \
  --resource-group rg-health-manager-dev \
  --name app-health-manager-dev
```

---

## Additional Resources

- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure PostgreSQL Documentation](https://docs.microsoft.com/en-us/azure/postgresql/)
- [Azure Cosmos DB Documentation](https://docs.microsoft.com/en-us/azure/cosmos-db/)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure CLI Reference](https://docs.microsoft.com/en-us/cli/azure/)

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review Azure Service Health dashboard
3. Check Application Insights for errors
4. Open an issue on the project repository
5. Contact DevOps team
