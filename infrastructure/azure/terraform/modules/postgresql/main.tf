# PostgreSQL Flexible Server Module

variable "environment" { type = string }
variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "subnet_id" { type = string }
variable "admin_username" { type = string }
variable "admin_password" {
  type = string
  sensitive = true
}
variable "key_vault_id" { type = string }
variable "tags" { type = map(string) }

resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "psql-health-manager-${var.environment}"
  resource_group_name    = var.resource_group_name
  location               = var.location
  version                = "17"
  delegated_subnet_id    = var.subnet_id
  administrator_login    = var.admin_username
  administrator_password = var.admin_password
  zone                   = "1"

  storage_mb            = var.environment == "prod" ? 65536 : 32768
  sku_name              = var.environment == "prod" ? "GP_Standard_D4s_v3" : "GP_Standard_D2s_v3"
  backup_retention_days = var.environment == "prod" ? 35 : 7

  high_availability {
    mode                      = var.environment == "prod" ? "ZoneRedundant" : "Disabled"
    standby_availability_zone = var.environment == "prod" ? "2" : null
  }

  maintenance_window {
    day_of_week  = 0 # Sunday
    start_hour   = 2
    start_minute = 0
  }

  tags = var.tags
}

resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = "health_manager"
  server_id = azurerm_postgresql_flexible_server.main.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

resource "azurerm_postgresql_flexible_server_configuration" "max_connections" {
  name      = "max_connections"
  server_id = azurerm_postgresql_flexible_server.main.id
  value     = "200"
}

output "server_id" {
  value = azurerm_postgresql_flexible_server.main.id
}

output "server_fqdn" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}

output "database_name" {
  value = azurerm_postgresql_flexible_server_database.main.name
}

output "admin_username" {
  value = var.admin_username
}
