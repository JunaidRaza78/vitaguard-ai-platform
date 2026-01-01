# Terraform Outputs
# Agentic AI Family Health Manager

# ==========================================
# GENERAL OUTPUTS
# ==========================================
output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "location" {
  description = "Azure region"
  value       = azurerm_resource_group.main.location
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

# ==========================================
# APP SERVICE OUTPUTS
# ==========================================
output "app_service_url" {
  description = "URL of the App Service"
  value       = "https://${azurerm_linux_web_app.main.default_hostname}"
}

output "app_service_name" {
  description = "Name of the App Service"
  value       = azurerm_linux_web_app.main.name
}

output "app_service_identity" {
  description = "Managed identity of the App Service"
  value       = azurerm_linux_web_app.main.identity[0].principal_id
}

# ==========================================
# CONTAINER REGISTRY OUTPUTS
# ==========================================
output "container_registry_url" {
  description = "URL of the Container Registry"
  value       = azurerm_container_registry.main.login_server
}

output "container_registry_name" {
  description = "Name of the Container Registry"
  value       = azurerm_container_registry.main.name
}

# ==========================================
# DATABASE OUTPUTS
# ==========================================
output "postgres_server_fqdn" {
  description = "PostgreSQL server FQDN"
  value       = module.postgresql.server_fqdn
}

output "postgres_database_name" {
  description = "PostgreSQL database name"
  value       = module.postgresql.database_name
}

output "neo4j_uri" {
  description = "Neo4j connection URI"
  value       = module.neo4j.connection_uri
}

output "neo4j_bolt_url" {
  description = "Neo4j Bolt URL"
  value       = module.neo4j.bolt_url
}

output "redis_hostname" {
  description = "Redis hostname"
  value       = azurerm_redis_cache.main.hostname
}

output "redis_port" {
  description = "Redis SSL port"
  value       = azurerm_redis_cache.main.ssl_port
}

# ==========================================
# KEY VAULT OUTPUTS
# ==========================================
output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

# ==========================================
# STORAGE OUTPUTS
# ==========================================
output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.main.name
}

output "storage_primary_endpoint" {
  description = "Primary blob endpoint"
  value       = azurerm_storage_account.main.primary_blob_endpoint
}

output "storage_containers" {
  description = "Storage container names"
  value = {
    medical_documents = azurerm_storage_container.medical_documents.name
    conversations     = azurerm_storage_container.conversations.name
    chat_messages     = azurerm_storage_container.chat_messages.name
    user_uploads      = azurerm_storage_container.user_uploads.name
    backups           = azurerm_storage_container.backups.name
  }
}

# ==========================================
# MONITORING OUTPUTS
# ==========================================
output "application_insights_instrumentation_key" {
  description = "Application Insights instrumentation key"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "application_insights_connection_string" {
  description = "Application Insights connection string"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID"
  value       = azurerm_log_analytics_workspace.main.id
}

# ==========================================
# NETWORK OUTPUTS
# ==========================================
output "virtual_network_name" {
  description = "Name of the virtual network"
  value       = azurerm_virtual_network.main.name
}

output "app_service_subnet_id" {
  description = "App Service subnet ID"
  value       = azurerm_subnet.app_service.id
}

# ==========================================
# SUMMARY OUTPUT
# ==========================================
output "deployment_summary" {
  description = "Deployment summary"
  value = {
    environment          = var.environment
    resource_group       = azurerm_resource_group.main.name
    app_service_url      = "https://${azurerm_linux_web_app.main.default_hostname}"
    container_registry   = azurerm_container_registry.main.login_server
    postgres_server      = module.postgresql.server_fqdn
    neo4j_bolt_url       = module.neo4j.bolt_url
    redis_hostname       = azurerm_redis_cache.main.hostname
    key_vault_name       = azurerm_key_vault.main.name
    storage_account_name = azurerm_storage_account.main.name
  }
}
