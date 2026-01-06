# Terraform Main Configuration
# Agentic AI Family Health Manager - Azure Infrastructure

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5.0"
    }
  }

  backend "azurerm" {
    # Backend configuration provided via CLI
    # -backend-config flags during terraform init
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = false
      recover_soft_deleted_key_vaults = true
    }
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# ==========================================
# LOCALS
# ==========================================
locals {
  common_tags = {
    Project     = "Agentic AI Family Health Manager"
    Environment = var.environment
    ManagedBy   = "Terraform"
    CreatedAt   = timestamp()
  }

  name_prefix = "health-manager-${var.environment}"
}

# ==========================================
# RESOURCE GROUP
# ==========================================
resource "azurerm_resource_group" "main" {
  name     = "rg-${local.name_prefix}"
  location = var.location
  tags     = local.common_tags
}

# ==========================================
# VIRTUAL NETWORK
# ==========================================
resource "azurerm_virtual_network" "main" {
  name                = "vnet-${local.name_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  address_space       = ["10.0.0.0/16"]
  tags                = local.common_tags
}

# Subnet for App Service VNet Integration
resource "azurerm_subnet" "app_service" {
  name                 = "snet-app-service"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]

  delegation {
    name = "app-service-delegation"
    service_delegation {
      name    = "Microsoft.Web/serverFarms"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}

# Subnet for Private Endpoints
resource "azurerm_subnet" "private_endpoints" {
  name                 = "snet-private-endpoints"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.2.0/24"]
}

# Subnet for Databases
resource "azurerm_subnet" "databases" {
  name                 = "snet-databases"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.3.0/24"]

  service_endpoints = [
    "Microsoft.Storage",
    "Microsoft.Sql",
    "Microsoft.KeyVault"
  ]
}

# ==========================================
# CONTAINER REGISTRY
# ==========================================
resource "azurerm_container_registry" "main" {
  name                = "crhealthmanager${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.environment == "prod" ? "Premium" : "Standard"
  admin_enabled       = true

  network_rule_set {
    default_action = "Deny"

    ip_rule {
      action   = "Allow"
      ip_range = "0.0.0.0/0" # Update with specific IPs in production
    }

    virtual_network {
      action    = "Allow"
      subnet_id = azurerm_subnet.app_service.id
    }
  }

  georeplications = var.environment == "prod" ? [
    {
      location                = "westus2"
      zone_redundancy_enabled = true
    }
  ] : []

  tags = local.common_tags
}

# ==========================================
# APP SERVICE PLAN
# ==========================================
resource "azurerm_service_plan" "main" {
  name                = "asp-${local.name_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = var.app_service_sku

  tags = local.common_tags
}

# ==========================================
# APP SERVICE (WEB APP)
# ==========================================
resource "azurerm_linux_web_app" "main" {
  name                = "app-${local.name_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.main.id

  https_only = true

  site_config {
    always_on                         = var.environment == "prod" ? true : false
    http2_enabled                     = true
    minimum_tls_version               = "1.2"
    ftps_state                        = "Disabled"
    vnet_route_all_enabled            = true
    container_registry_use_managed_identity = true

    application_stack {
      docker_image_name   = "${azurerm_container_registry.main.login_server}/health-manager:latest"
      docker_registry_url = "https://${azurerm_container_registry.main.login_server}"
    }

    health_check_path                 = "/health"
    health_check_eviction_time_in_min = 5

    cors {
      allowed_origins = var.allowed_origins
      support_credentials = true
    }
  }

  identity {
    type = "SystemAssigned"
  }

  app_settings = {
    # Application Settings
    ENVIRONMENT                         = var.environment
    DOCKER_ENABLE_CI                    = "true"
    WEBSITES_ENABLE_APP_SERVICE_STORAGE = "false"

    # Database Configuration (from Key Vault)
    POSTGRES_HOST     = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.postgres_host.id})"
    POSTGRES_PORT     = "5432"
    POSTGRES_DB       = "health_manager"
    POSTGRES_USER     = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.postgres_user.id})"
    POSTGRES_PASSWORD = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.postgres_password.id})"

    NEO4J_URI      = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.neo4j_uri.id})"
    NEO4J_USER     = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.neo4j_user.id})"
    NEO4J_PASSWORD = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.neo4j_password.id})"

    REDIS_HOST     = azurerm_redis_cache.main.hostname
    REDIS_PORT     = azurerm_redis_cache.main.ssl_port
    REDIS_PASSWORD = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.redis_password.id})"
    REDIS_SSL      = "true"

    # API Keys
    OPENAI_API_KEY    = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.openai_api_key.id})"
    ANTHROPIC_API_KEY = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.anthropic_api_key.id})"
    SECRET_KEY        = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.app_secret_key.id})"

    # Storage
    AZURE_STORAGE_CONNECTION_STRING = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.storage_connection.id})"

    # Application Insights
    APPLICATIONINSIGHTS_CONNECTION_STRING = azurerm_application_insights.main.connection_string
  }

  logs {
    application_logs {
      file_system_level = "Information"
    }

    http_logs {
      file_system {
        retention_in_days = 7
        retention_in_mb   = 35
      }
    }
  }

  tags = local.common_tags
}

# Production Staging Slot
resource "azurerm_linux_web_app_slot" "staging" {
  count          = var.environment == "prod" ? 1 : 0
  name           = "staging"
  app_service_id = azurerm_linux_web_app.main.id

  site_config {
    always_on                         = true
    http2_enabled                     = true
    minimum_tls_version               = "1.2"
    container_registry_use_managed_identity = true

    application_stack {
      docker_image_name   = "${azurerm_container_registry.main.login_server}/health-manager:latest"
      docker_registry_url = "https://${azurerm_container_registry.main.login_server}"
    }
  }

  tags = local.common_tags
}

# VNet Integration
resource "azurerm_app_service_virtual_network_swift_connection" "main" {
  app_service_id = azurerm_linux_web_app.main.id
  subnet_id      = azurerm_subnet.app_service.id
}

# ==========================================
# KEY VAULT
# ==========================================
data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "main" {
  name                       = "kv-health-${var.environment}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 90
  purge_protection_enabled   = var.environment == "prod" ? true : false

  network_acls {
    bypass                     = "AzureServices"
    default_action             = "Deny"
    ip_rules                   = var.allowed_ip_ranges
    virtual_network_subnet_ids = [azurerm_subnet.app_service.id]
  }

  tags = local.common_tags
}

# Access Policy for App Service
resource "azurerm_key_vault_access_policy" "app_service" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_linux_web_app.main.identity[0].principal_id

  secret_permissions = [
    "Get",
    "List"
  ]
}

# Access Policy for Current User/Service Principal
resource "azurerm_key_vault_access_policy" "current" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = [
    "Get",
    "List",
    "Set",
    "Delete",
    "Purge",
    "Recover"
  ]
}

# ==========================================
# MODULE IMPORTS
# ==========================================
module "postgresql" {
  source = "./modules/postgresql"

  environment         = var.environment
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  subnet_id           = azurerm_subnet.databases.id
  admin_username      = var.postgres_admin_username
  admin_password      = var.postgres_admin_password
  key_vault_id        = azurerm_key_vault.main.id

  tags = local.common_tags

  depends_on = [azurerm_key_vault_access_policy.current]
}

module "neo4j" {
  source = "./modules/neo4j"

  environment         = var.environment
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  subnet_id           = azurerm_subnet.databases.id
  key_vault_id        = azurerm_key_vault.main.id

  tags = local.common_tags

  depends_on = [azurerm_key_vault_access_policy.current]
}

# ==========================================
# REDIS CACHE
# ==========================================
resource "azurerm_redis_cache" "main" {
  name                = "redis-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  capacity            = var.redis_capacity
  family              = var.redis_family
  sku_name            = var.redis_sku
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"

  redis_configuration {
    enable_authentication = true
    maxmemory_policy      = "allkeys-lru"
  }

  patch_schedule {
    day_of_week    = "Sunday"
    start_hour_utc = 2
  }

  tags = local.common_tags
}

# ==========================================
# STORAGE ACCOUNT
# ==========================================
resource "azurerm_storage_account" "main" {
  name                     = "sthealth${var.environment}${random_string.storage_suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = var.environment == "prod" ? "GRS" : "LRS"
  account_kind             = "StorageV2"
  min_tls_version          = "TLS1_2"
  enable_https_traffic_only = true

  blob_properties {
    versioning_enabled = true

    delete_retention_policy {
      days = 30
    }
  }

  network_rules {
    default_action             = "Deny"
    bypass                     = ["AzureServices"]
    ip_rules                   = var.allowed_ip_ranges
    virtual_network_subnet_ids = [azurerm_subnet.app_service.id]
  }

  tags = local.common_tags
}

resource "random_string" "storage_suffix" {
  length  = 6
  special = false
  upper   = false
}

# Storage Containers (Buckets) for different data types
resource "azurerm_storage_container" "medical_documents" {
  name                  = "medical-documents"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "conversations" {
  name                  = "conversations"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "chat_messages" {
  name                  = "chat-messages"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "user_uploads" {
  name                  = "user-uploads"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "backups" {
  name                  = "backups"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Storage Lifecycle Management
resource "azurerm_storage_management_policy" "main" {
  storage_account_id = azurerm_storage_account.main.id

  rule {
    name    = "archive-old-documents"
    enabled = true

    filters {
      prefix_match = ["medical-documents/", "user-uploads/"]
      blob_types   = ["blockBlob"]
    }

    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than    = 90
        tier_to_archive_after_days_since_modification_greater_than = 365
        delete_after_days_since_modification_greater_than          = var.environment == "prod" ? 2555 : 730 # 7 years prod, 2 years dev
      }

      snapshot {
        delete_after_days_since_creation_greater_than = 30
      }
    }
  }

  rule {
    name    = "cleanup-old-chat-data"
    enabled = var.environment != "prod" # Only for dev/staging

    filters {
      prefix_match = ["conversations/", "chat-messages/"]
      blob_types   = ["blockBlob"]
    }

    actions {
      base_blob {
        delete_after_days_since_modification_greater_than = 90
      }
    }
  }
}

# ==========================================
# APPLICATION INSIGHTS
# ==========================================
resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = var.environment == "prod" ? 90 : 30

  tags = local.common_tags
}

resource "azurerm_application_insights" "main" {
  name                = "appi-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"

  tags = local.common_tags
}

# ==========================================
# KEY VAULT SECRETS
# ==========================================
resource "azurerm_key_vault_secret" "postgres_host" {
  name         = "postgres-host"
  value        = module.postgresql.server_fqdn
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current]
}

resource "azurerm_key_vault_secret" "postgres_user" {
  name         = "postgres-user"
  value        = module.postgresql.admin_username
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current]
}

resource "azurerm_key_vault_secret" "postgres_password" {
  name         = "postgres-password"
  value        = var.postgres_admin_password
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current]
}

resource "azurerm_key_vault_secret" "neo4j_uri" {
  name         = "neo4j-uri"
  value        = module.neo4j.connection_uri
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current]
}

resource "azurerm_key_vault_secret" "neo4j_user" {
  name         = "neo4j-user"
  value        = module.neo4j.admin_username
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current]
}

resource "azurerm_key_vault_secret" "neo4j_password" {
  name         = "neo4j-password"
  value        = module.neo4j.admin_password
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current]
}

resource "azurerm_key_vault_secret" "redis_password" {
  name         = "redis-password"
  value        = azurerm_redis_cache.main.primary_access_key
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current]
}

resource "azurerm_key_vault_secret" "storage_connection" {
  name         = "storage-connection-string"
  value        = azurerm_storage_account.main.primary_connection_string
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current]
}

# Placeholder secrets (to be updated manually)
resource "azurerm_key_vault_secret" "openai_api_key" {
  name         = "openai-api-key"
  value        = var.openai_api_key != "" ? var.openai_api_key : "placeholder-update-manually"
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current]
}

resource "azurerm_key_vault_secret" "anthropic_api_key" {
  name         = "anthropic-api-key"
  value        = var.anthropic_api_key != "" ? var.anthropic_api_key : "placeholder-update-manually"
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current]
}

resource "azurerm_key_vault_secret" "app_secret_key" {
  name         = "app-secret-key"
  value        = random_password.app_secret.result
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current]
}

resource "random_password" "app_secret" {
  length  = 64
  special = true
}
