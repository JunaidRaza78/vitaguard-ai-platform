# MongoDB (Cosmos DB) Module

variable "environment" { type = string }
variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "key_vault_id" { type = string }
variable "tags" { type = map(string) }

resource "azurerm_cosmosdb_account" "main" {
  name                = "cosmos-health-manager-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  offer_type          = "Standard"
  kind                = "MongoDB"

  mongo_server_version = "7.0"

  consistency_policy {
    consistency_level       = "Session"
    max_interval_in_seconds = 5
    max_staleness_prefix    = 100
  }

  geo_location {
    location          = var.location
    failover_priority = 0
    zone_redundant    = var.environment == "prod" ? true : false
  }

  # Add secondary region for production
  dynamic "geo_location" {
    for_each = var.environment == "prod" ? [1] : []
    content {
      location          = "westus2"
      failover_priority = 1
      zone_redundant    = true
    }
  }

  capabilities {
    name = "EnableMongo"
  }

  capabilities {
    name = "MongoDBv3.4"
  }

  capabilities {
    name = "mongoEnableDocLevelTTL"
  }

  backup {
    type                = var.environment == "prod" ? "Continuous" : "Periodic"
    interval_in_minutes = var.environment == "prod" ? null : 240
    retention_in_hours  = var.environment == "prod" ? null : 8
  }

  automatic_failover_enabled = var.environment == "prod" ? true : false

  tags = var.tags
}

resource "azurerm_cosmosdb_mongo_database" "main" {
  name                = "health_manager"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
  throughput          = var.environment == "prod" ? 1000 : 400
}

# Collections
resource "azurerm_cosmosdb_mongo_collection" "conversations" {
  name                = "conversations"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_mongo_database.main.name

  index {
    keys   = ["_id"]
    unique = true
  }

  index {
    keys   = ["conversationId"]
    unique = true
  }

  index {
    keys = ["userId", "startTime"]
  }
}

resource "azurerm_cosmosdb_mongo_collection" "messages" {
  name                = "messages"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_mongo_database.main.name

  index {
    keys   = ["_id"]
    unique = true
  }

  index {
    keys = ["conversationId", "createdAt"]
  }
}

resource "azurerm_cosmosdb_mongo_collection" "medical_documents" {
  name                = "medical_documents"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_mongo_database.main.name

  index {
    keys   = ["_id"]
    unique = true
  }

  index {
    keys = ["userId", "documentType"]
  }
}

output "account_id" {
  value = azurerm_cosmosdb_account.main.id
}

output "connection_string" {
  value     = azurerm_cosmosdb_account.main.connection_strings[0]
  sensitive = true
}

output "endpoint" {
  value = azurerm_cosmosdb_account.main.endpoint
}

output "database_name" {
  value = azurerm_cosmosdb_mongo_database.main.name
}
