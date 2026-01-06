# Azure Infrastructure Quick Start Guide

Fast-track guide to deploy the Agentic AI Family Health Manager on Azure.

## Prerequisites Checklist

- [ ] Azure Subscription with active credits
- [ ] Azure CLI installed and authenticated
- [ ] Terraform installed (v1.5+)
- [ ] Docker installed
- [ ] Git repository cloned
- [ ] GitHub account (for CI/CD)

## 🚀 5-Minute Setup

### Step 1: Azure Login

```bash
az login
az account set --subscription "Your Subscription Name"
```

### Step 2: Create Service Principal

```bash
# Create service principal for CI/CD
az ad sp create-for-rbac \
  --name "sp-health-manager" \
  --role Contributor \
  --scopes /subscriptions/$(az account show --query id -o tsv) \
  --sdk-auth > azure-credentials.json

# Save this output for GitHub Secrets
cat azure-credentials.json
```

### Step 3: Create Terraform Backend

```bash
# Create storage account for Terraform state
RESOURCE_GROUP="rg-health-tfstate"
STORAGE_ACCOUNT="sthealthtfstate$(openssl rand -hex 3)"
LOCATION="eastus"

az group create --name $RESOURCE_GROUP --location $LOCATION

az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --encryption-services blob

az storage container create \
  --name tfstate \
  --account-name $STORAGE_ACCOUNT

echo "Backend Storage Account: $STORAGE_ACCOUNT"
```

### Step 4: Configure GitHub Secrets

Go to **GitHub Repository → Settings → Secrets and variables → Actions**

Add these secrets:

| Secret Name | Value Source | How to Get |
|-------------|--------------|------------|
| `AZURE_CREDENTIALS_DEV` | `azure-credentials.json` content | From Step 2 |
| `AZURE_CREDENTIALS_STAGING` | Same as dev (or create separate) | From Step 2 |
| `AZURE_CREDENTIALS_PROD` | Same as dev (or create separate) | From Step 2 |
| `ACR_USERNAME` | Will be created by Terraform | After first deploy |
| `ACR_PASSWORD` | Will be created by Terraform | After first deploy |

### Step 5: Deploy Infrastructure

```bash
cd infrastructure/azure/terraform

# Initialize Terraform
terraform init \
  -backend-config="resource_group_name=$RESOURCE_GROUP" \
  -backend-config="storage_account_name=$STORAGE_ACCOUNT" \
  -backend-config="container_name=tfstate" \
  -backend-config="key=dev.terraform.tfstate"

# Create variables file
cat > dev.tfvars <<EOF
environment = "dev"
location = "eastus"
postgres_admin_username = "pgadmin"
postgres_admin_password = "ChangeMe123!@#"
EOF

# Deploy
terraform plan -var-file="dev.tfvars" -out=tfplan
terraform apply tfplan

# Save outputs
terraform output -json > outputs.json
```

### Step 6: Configure Secrets in Key Vault

```bash
# Get Key Vault name from Terraform output
KEY_VAULT=$(terraform output -raw key_vault_name)

# Set API keys (replace with your actual keys)
az keyvault secret set \
  --vault-name $KEY_VAULT \
  --name openai-api-key \
  --value "sk-your-openai-key-here"

az keyvault secret set \
  --vault-name $KEY_VAULT \
  --name anthropic-api-key \
  --value "sk-ant-your-anthropic-key-here"
```

### Step 7: Get ACR Credentials for GitHub

```bash
# Get ACR name from Terraform
ACR_NAME=$(terraform output -raw container_registry_name)

# Get credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

echo "ACR_USERNAME: $ACR_USERNAME"
echo "ACR_PASSWORD: $ACR_PASSWORD"

# Add these to GitHub Secrets (Step 4)
```

### Step 8: Deploy Application

```bash
# Option A: Using GitHub Actions (Recommended)
git checkout -b develop
git push origin develop
# GitHub Actions will automatically build and deploy

# Option B: Manual deployment
cd ../../..  # Back to root
docker build -t health-manager:latest -f Backend/Dockerfile .

az acr login --name $ACR_NAME
docker tag health-manager:latest $ACR_NAME.azurecr.io/health-manager:latest
docker push $ACR_NAME.azurecr.io/health-manager:latest

# Get App Service name
APP_NAME=$(cd infrastructure/azure/terraform && terraform output -raw app_service_name)

# Restart App Service
az webapp restart --resource-group rg-health-manager-dev --name $APP_NAME
```

### Step 9: Verify Deployment

```bash
# Get application URL
APP_URL=$(cd infrastructure/azure/terraform && terraform output -raw app_service_url)

echo "Application URL: $APP_URL"

# Test health endpoint
curl $APP_URL/health

# Expected response: {"status": "healthy", "databases": {...}}
```

### Step 10: Access Services

```bash
# Application
echo "App: https://app-health-manager-dev.azurewebsites.net"

# Neo4j Browser (via SSH tunnel)
NEO4J_IP=$(cd infrastructure/azure/terraform && terraform output -json | jq -r '.neo4j_uri.value' | cut -d'/' -f3 | cut -d':' -f1)
ssh -L 7474:localhost:7474 -L 7687:localhost:7687 neo4jadmin@$NEO4J_IP
# Then open: http://localhost:7474

# PostgreSQL
POSTGRES_HOST=$(cd infrastructure/azure/terraform && terraform output -raw postgres_server_fqdn)
psql "host=$POSTGRES_HOST port=5432 dbname=health_manager user=pgadmin sslmode=require"
```

---

## Common Commands

### Monitor Application

```bash
# Stream logs
az webapp log tail --resource-group rg-health-manager-dev --name app-health-manager-dev

# Download logs
az webapp log download --resource-group rg-health-manager-dev --name app-health-manager-dev

# Check metrics
az monitor metrics list \
  --resource /subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-health-manager-dev/providers/Microsoft.Web/sites/app-health-manager-dev \
  --metric "CpuPercentage" "MemoryPercentage" "HttpResponseTime"
```

### Database Operations

```bash
# Connect to PostgreSQL
az postgres flexible-server connect \
  --name psql-health-manager-dev \
  --admin-user pgadmin \
  --database health_manager

# MongoDB connection string
MONGO_CONN=$(az cosmosdb keys list \
  --resource-group rg-health-manager-dev \
  --name cosmos-health-manager-dev \
  --type connection-strings \
  --query "connectionStrings[0].connectionString" -o tsv)
mongosh "$MONGO_CONN"

# Check Redis
REDIS_HOST=$(az redis show \
  --resource-group rg-health-manager-dev \
  --name redis-health-manager-dev \
  --query hostName -o tsv)
REDIS_KEY=$(az redis list-keys \
  --resource-group rg-health-manager-dev \
  --name redis-health-manager-dev \
  --query primaryKey -o tsv)
redis-cli -h $REDIS_HOST -p 6380 -a $REDIS_KEY --tls
```

### Scale Application

```bash
# Scale up (increase VM size)
az appservice plan update \
  --resource-group rg-health-manager-dev \
  --name asp-health-manager-dev \
  --sku P2v3

# Scale out (increase instances)
az appservice plan update \
  --resource-group rg-health-manager-dev \
  --name asp-health-manager-dev \
  --number-of-workers 3
```

---

## Branching Strategy for CI/CD

```bash
# Development environment
git checkout develop
git push origin develop
# → Deploys to: app-health-manager-dev.azurewebsites.net

# Staging environment
git checkout -b release/v1.0.0
git push origin release/v1.0.0
# → Deploys to: app-health-manager-staging.azurewebsites.net

# Production environment
git checkout main
git merge release/v1.0.0
git push origin main
# → Deploys to: app-health-manager-prod.azurewebsites.net (blue-green)
```

---

## Cost Estimation

### Development Environment
```
App Service P1v3:        $100/month
PostgreSQL GP_D2s_v3:    $120/month
Cosmos DB (400 RU/s):    $24/month
Neo4j VM D2s_v3:         $70/month
Redis Standard:          $15/month
Storage:                 $10/month
Monitoring:              $20/month
─────────────────────────────────
Total:                   ~$360/month
```

### Production Environment
```
App Service P3v3:        $400/month
PostgreSQL GP_D4s_v3+HA: $350/month
Cosmos DB (4000 RU/s):   $470/month
Neo4j VM D4s_v3:         $200/month
Redis Premium:           $180/month
Storage (with backup):   $50/month
Monitoring:              $100/month
Front Door (optional):   $300/month
─────────────────────────────────
Total:                   ~$2,050/month
```

---

## Troubleshooting

### Issue: Terraform Backend Error

```bash
# Fix: Ensure backend storage exists
az storage account show --name $STORAGE_ACCOUNT
az storage container show --name tfstate --account-name $STORAGE_ACCOUNT
```

### Issue: Container Registry Login Failed

```bash
# Fix: Enable admin user
az acr update --name $ACR_NAME --admin-enabled true

# Get new credentials
az acr credential show --name $ACR_NAME
```

### Issue: App Service 503 Error

```bash
# Check if container is running
az webapp show \
  --resource-group rg-health-manager-dev \
  --name app-health-manager-dev \
  --query "state"

# Check logs
az webapp log tail \
  --resource-group rg-health-manager-dev \
  --name app-health-manager-dev
```

### Issue: Database Connection Timeout

```bash
# Check if VNet integration is working
az webapp vnet-integration list \
  --resource-group rg-health-manager-dev \
  --name app-health-manager-dev

# Check database firewall rules
az postgres flexible-server firewall-rule list \
  --resource-group rg-health-manager-dev \
  --name psql-health-manager-dev
```

---

## Clean Up (Delete Everything)

⚠️ **WARNING**: This will delete all resources and data!

```bash
# Option 1: Using Terraform
cd infrastructure/azure/terraform
terraform destroy -var-file="dev.tfvars" -auto-approve

# Option 2: Delete resource group
az group delete --name rg-health-manager-dev --yes --no-wait

# Delete Terraform state storage (if needed)
az group delete --name rg-health-tfstate --yes
```

---

## Next Steps

1. ✅ Infrastructure deployed
2. ⏭️ Configure custom domain and SSL
3. ⏭️ Set up monitoring alerts
4. ⏭️ Configure backup policies
5. ⏭️ Enable Azure Front Door for global distribution
6. ⏭️ Implement disaster recovery plan
7. ⏭️ Security hardening and penetration testing

---

## Support

- 📖 Full Documentation: [README.md](./README.md)
- 🔧 Troubleshooting: [README.md#troubleshooting](./README.md#troubleshooting)
- 💬 Issues: [GitHub Issues](https://github.com/yourusername/agentic-ai-family-health-manager/issues)
