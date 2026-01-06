# Azure Deployment Checklist

Use this checklist to ensure a successful deployment of the Agentic AI Family Health Manager on Azure.

---

## 📋 Pre-Deployment Checklist

### Azure Account Setup
- [ ] Azure subscription is active with sufficient credits
- [ ] You have Owner or Contributor role on the subscription
- [ ] Billing alerts configured
- [ ] Resource quotas checked (VM cores, public IPs, etc.)

### Tools Installation
- [ ] Azure CLI installed (`az --version`)
- [ ] Terraform installed v1.5+ (`terraform --version`)
- [ ] Docker installed (`docker --version`)
- [ ] Git installed (`git --version`)
- [ ] kubectl installed (if using AKS) (`kubectl version --client`)
- [ ] jq installed for JSON parsing (`jq --version`)

### Repository Setup
- [ ] Repository cloned locally
- [ ] SSH key generated (`ssh-keygen -t rsa -b 4096`)
- [ ] SSH public key available at `~/.ssh/id_rsa.pub`
- [ ] Git configured with your email and name

---

## 🔐 Security & Access

### Service Principal Creation
- [ ] Service principal created for CI/CD
  ```bash
  az ad sp create-for-rbac --name "sp-health-manager" --role Contributor --sdk-auth
  ```
- [ ] Service principal credentials saved securely
- [ ] Service principal has required permissions:
  - [ ] Contributor on subscription
  - [ ] Key Vault Administrator
  - [ ] Storage Blob Data Contributor

### SSH Access
- [ ] SSH key generated for Neo4j VM access
- [ ] SSH key added to ssh-agent
  ```bash
  eval "$(ssh-agent -s)"
  ssh-add ~/.ssh/id_rsa
  ```

### API Keys
- [ ] OpenAI API key obtained
- [ ] Anthropic API key obtained
- [ ] Keys stored securely (password manager)

---

## 🏗️ Infrastructure Setup

### Terraform Backend Storage
- [ ] Resource group created for Terraform state
  ```bash
  az group create --name rg-health-tfstate --location eastus
  ```
- [ ] Storage account created
  ```bash
  STORAGE_ACCOUNT="sthealthtfstate$(openssl rand -hex 3)"
  az storage account create --name $STORAGE_ACCOUNT --resource-group rg-health-tfstate
  ```
- [ ] Storage container created
  ```bash
  az storage container create --name tfstate --account-name $STORAGE_ACCOUNT
  ```
- [ ] Storage account name documented

### Terraform Configuration
- [ ] Backend configuration file created (`backend-config.hcl`)
- [ ] Variables file created for dev (`dev.tfvars`)
- [ ] Variables file created for staging (`staging.tfvars`)
- [ ] Variables file created for prod (`prod.tfvars`)
- [ ] PostgreSQL admin password generated (min 12 chars, complex)
- [ ] Terraform initialized
  ```bash
  terraform init -backend-config="backend-config.hcl"
  ```

---

## 🚀 CI/CD Configuration

### GitHub Setup (if using GitHub Actions)
- [ ] Repository pushed to GitHub
- [ ] GitHub Actions enabled
- [ ] Secrets added to GitHub:
  - [ ] `AZURE_CREDENTIALS_DEV`
  - [ ] `AZURE_CREDENTIALS_STAGING`
  - [ ] `AZURE_CREDENTIALS_PROD`
  - [ ] `ACR_USERNAME` (added after first Terraform apply)
  - [ ] `ACR_PASSWORD` (added after first Terraform apply)
- [ ] Branch protection rules configured:
  - [ ] `main` branch requires PR review
  - [ ] `develop` branch allows direct commits (dev team only)

### Azure DevOps Setup (if using Azure DevOps)
- [ ] Azure DevOps project created
- [ ] Pipeline imported from `.azure/pipelines/azure-pipelines.yml`
- [ ] Service connection configured
- [ ] Variable groups created:
  - [ ] `dev-variables`
  - [ ] `staging-variables`
  - [ ] `prod-variables`
- [ ] Key Vault linked to variable groups
- [ ] Pipeline permissions granted

---

## 🗄️ Database Configuration

### PostgreSQL
- [ ] Admin username decided (no 'admin', 'root', 'postgres')
- [ ] Strong password generated and saved
- [ ] Firewall rules planned
- [ ] Backup retention configured (7 days dev, 35 days prod)

### MongoDB (Cosmos DB)
- [ ] Throughput requirements calculated
- [ ] Consistency level decided (Session recommended)
- [ ] Geo-replication regions selected (prod only)

### Neo4j
- [ ] VM size selected based on environment
- [ ] Data disk size calculated
- [ ] Network access planned

### Redis
- [ ] SKU selected based on environment
- [ ] Maxmemory policy configured (allkeys-lru)
- [ ] Persistence enabled for prod

---

## 🌐 Network Configuration

### Virtual Network
- [ ] Address space planned (10.0.0.0/16 default)
- [ ] Subnet ranges calculated:
  - [ ] App Service: 10.0.1.0/24
  - [ ] Private Endpoints: 10.0.2.0/24
  - [ ] Databases: 10.0.3.0/24

### Firewall Rules
- [ ] Allowed IP ranges documented
- [ ] Service endpoints configured
- [ ] Private endpoints planned

### DNS Configuration (Optional)
- [ ] Custom domain purchased
- [ ] DNS provider selected
- [ ] SSL certificate obtained or planned (Let's Encrypt/Azure Managed)

---

## 📦 Application Configuration

### Docker
- [ ] Dockerfile reviewed and tested locally
- [ ] .dockerignore configured
- [ ] Multi-stage build verified
- [ ] Image size optimized (<500MB recommended)

### Environment Variables
- [ ] All required environment variables documented
- [ ] Sensitive values identified for Key Vault
- [ ] Non-sensitive values prepared for App Settings

### Health Checks
- [ ] Health check endpoint implemented (`/health`)
- [ ] Database connectivity checks included
- [ ] Response time acceptable (<5 seconds)

---

## 🔍 Monitoring & Logging

### Application Insights
- [ ] Instrumentation key planned
- [ ] Sampling rate configured (100% dev, 10-50% prod)
- [ ] Custom metrics identified

### Log Analytics
- [ ] Retention period configured (30 days dev, 90 days prod)
- [ ] Log queries prepared
- [ ] Dashboards planned

### Alerts
- [ ] Critical alerts defined:
  - [ ] Application down
  - [ ] High error rate
  - [ ] Database connection failures
  - [ ] High memory usage
- [ ] Alert action groups configured
- [ ] Notification channels set up (email, SMS, Teams)

---

## 💰 Cost Management

### Budget Alerts
- [ ] Monthly budget set for dev ($500)
- [ ] Monthly budget set for staging ($800)
- [ ] Monthly budget set for prod ($2,500)
- [ ] Alert thresholds configured (50%, 75%, 90%, 100%)
- [ ] Alert recipients added

### Cost Optimization
- [ ] Auto-shutdown configured for dev VMs (7 PM daily)
- [ ] Auto-shutdown configured for staging VMs (weekends)
- [ ] Reserved instances considered for prod
- [ ] Cosmos DB autoscale enabled

---

## 🚀 Deployment Execution

### Initial Infrastructure Deployment
- [ ] Terraform plan reviewed
  ```bash
  terraform plan -var-file="dev.tfvars" -out=tfplan
  ```
- [ ] Terraform plan approved by team lead
- [ ] Terraform applied
  ```bash
  terraform apply tfplan
  ```
- [ ] Outputs saved
  ```bash
  terraform output -json > outputs.json
  ```

### Secret Configuration
- [ ] Key Vault access verified
- [ ] OpenAI API key set in Key Vault
- [ ] Anthropic API key set in Key Vault
- [ ] Connection strings verified
- [ ] Managed Identity access tested

### Container Registry
- [ ] ACR credentials retrieved
  ```bash
  az acr credential show --name <acr-name>
  ```
- [ ] Credentials added to GitHub/Azure DevOps
- [ ] Test login successful
  ```bash
  az acr login --name <acr-name>
  ```

### Application Deployment
- [ ] Docker image built locally (test)
- [ ] Docker image pushed to ACR (test)
- [ ] CI/CD pipeline triggered
- [ ] Pipeline succeeded
- [ ] Application restarted
  ```bash
  az webapp restart --resource-group <rg> --name <app-name>
  ```

---

## ✅ Post-Deployment Verification

### Application Health
- [ ] Health endpoint accessible
  ```bash
  curl https://app-health-manager-dev.azurewebsites.net/health
  ```
- [ ] Response status: 200 OK
- [ ] All database connections: healthy
- [ ] Response time: <5 seconds

### Database Connectivity
- [ ] PostgreSQL connection successful
  ```bash
  psql "host=<fqdn> port=5432 dbname=health_manager user=<user> sslmode=require"
  ```
- [ ] MongoDB connection successful
  ```bash
  mongosh "<connection-string>"
  ```
- [ ] Neo4j accessible
  ```bash
  # Via SSH tunnel
  ssh -L 7474:localhost:7474 neo4jadmin@<neo4j-ip>
  # Open: http://localhost:7474
  ```
- [ ] Redis connection successful
  ```bash
  redis-cli -h <host> -p 6380 -a <key> --tls
  ```

### Monitoring
- [ ] Application Insights receiving telemetry
- [ ] Logs appearing in Log Analytics
  ```bash
  az monitor app-insights query --app <app-name> --analytics-query "traces | take 10"
  ```
- [ ] Custom metrics working
- [ ] Performance metrics within acceptable range

### Security Verification
- [ ] HTTPS enforced (no HTTP access)
- [ ] SSL certificate valid
- [ ] Managed Identity working
- [ ] Key Vault secrets accessible
- [ ] No secrets in App Settings (all in Key Vault)
- [ ] CORS configured correctly
- [ ] Network isolation verified

### Functional Testing
- [ ] User registration works
- [ ] User login works
- [ ] API endpoints respond correctly
- [ ] File upload works
- [ ] Database queries execute
- [ ] Chat functionality works

---

## 🔄 CI/CD Verification

### GitHub Actions
- [ ] Workflow triggered on commit to `develop`
- [ ] Build stage passed
- [ ] Test stage passed
- [ ] Deploy stage passed
- [ ] Health check passed

### Branch Strategy
- [ ] `develop` → deploys to dev
- [ ] `release/*` → deploys to staging
- [ ] `main` → deploys to prod (blue-green)

---

## 📝 Documentation

### Updated Documentation
- [ ] Architecture diagram updated
- [ ] Connection strings documented (securely)
- [ ] Environment variables documented
- [ ] Deployment procedures documented
- [ ] Troubleshooting guide updated
- [ ] Runbook created for common operations

### Team Knowledge Transfer
- [ ] Team walkthrough scheduled
- [ ] Azure Portal access granted
- [ ] Repository access granted
- [ ] On-call rotation defined
- [ ] Escalation procedures documented

---

## 🎯 Production Readiness (Before Prod Deployment)

### Performance Testing
- [ ] Load testing completed (minimum 1000 concurrent users)
- [ ] Stress testing completed
- [ ] Response times acceptable (<200ms p95)
- [ ] Database performance verified
- [ ] Auto-scaling tested

### Security Audit
- [ ] Penetration testing completed
- [ ] Vulnerability scan completed
- [ ] HIPAA compliance verified
- [ ] Security review by team
- [ ] Azure Security Center recommendations addressed

### Disaster Recovery
- [ ] Backup policies verified
- [ ] Restore procedures tested
- [ ] RTO/RPO targets defined
- [ ] DR runbook created
- [ ] DR testing scheduled

### Legal & Compliance
- [ ] Privacy policy updated
- [ ] Terms of service updated
- [ ] HIPAA BAA signed with Microsoft
- [ ] Data processing agreement signed
- [ ] Compliance audit completed

---

## 🚨 Rollback Plan

### Rollback Procedures Documented
- [ ] App Service slot swap revert procedure
- [ ] Database rollback procedure
- [ ] Terraform state rollback
- [ ] Docker image version rollback

### Rollback Testing
- [ ] Rollback procedure tested in staging
- [ ] Rollback script created
- [ ] Rollback contact list created

---

## 📊 Success Criteria

### Deployment Success
- [ ] All services running
- [ ] Health checks passing
- [ ] No errors in logs (first hour)
- [ ] Response times acceptable
- [ ] User acceptance testing passed

### Monitoring Success
- [ ] All metrics collecting
- [ ] Alerts configured and tested
- [ ] Dashboards accessible
- [ ] On-call rotation active

### Business Success
- [ ] Stakeholders informed
- [ ] Go-live announcement sent
- [ ] Support team trained
- [ ] Users onboarded

---

## 🎉 Completion

**Deployment Date**: ________________

**Deployed By**: ________________

**Verified By**: ________________

**Notes**:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

## 📞 Emergency Contacts

| Role | Name | Contact | Backup |
|------|------|---------|--------|
| DevOps Lead | | | |
| Azure Admin | | | |
| Database Admin | | | |
| Security Lead | | | |
| Product Owner | | | |

---

**Last Updated**: 2024-01-20

For detailed instructions, see:
- [Quick Start Guide](./QUICK_START.md)
- [Full Documentation](./README.md)
