# Terraform Variables
# Agentic AI Family Health Manager

# ==========================================
# GENERAL VARIABLES
# ==========================================
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "allowed_ip_ranges" {
  description = "List of allowed IP ranges for network access"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Update in production
}

variable "allowed_origins" {
  description = "List of allowed CORS origins"
  type        = list(string)
  default     = ["*"] # Update in production
}

# ==========================================
# APP SERVICE VARIABLES
# ==========================================
variable "app_service_sku" {
  description = "SKU for App Service Plan"
  type        = string
  default     = "P1v3"
}

# ==========================================
# POSTGRESQL VARIABLES
# ==========================================
variable "postgres_admin_username" {
  description = "PostgreSQL administrator username"
  type        = string
  default     = "pgadmin"
  sensitive   = true
}

variable "postgres_admin_password" {
  description = "PostgreSQL administrator password"
  type        = string
  sensitive   = true
}

variable "postgres_sku_name" {
  description = "PostgreSQL SKU name"
  type        = string
  default     = "GP_Standard_D2s_v3"
}

variable "postgres_storage_mb" {
  description = "PostgreSQL storage size in MB"
  type        = number
  default     = 32768 # 32GB
}

# ==========================================
# REDIS VARIABLES
# ==========================================
variable "redis_capacity" {
  description = "Redis cache capacity"
  type        = number
  default     = 1
}

variable "redis_family" {
  description = "Redis cache family"
  type        = string
  default     = "P" # Premium
}

variable "redis_sku" {
  description = "Redis cache SKU"
  type        = string
  default     = "Premium"
}

# ==========================================
# MONGODB VARIABLES
# ==========================================
variable "mongodb_tier" {
  description = "MongoDB Cosmos DB tier"
  type        = string
  default     = "M10"
}

# ==========================================
# NEO4J VARIABLES
# ==========================================
variable "neo4j_version" {
  description = "Neo4j version"
  type        = string
  default     = "5.15.0"
}

variable "neo4j_vm_size" {
  description = "Neo4j VM size"
  type        = string
  default     = "Standard_D2s_v3"
}

# ==========================================
# API KEYS (Optional - can be set manually in Key Vault)
# ==========================================
variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "anthropic_api_key" {
  description = "Anthropic API key"
  type        = string
  default     = ""
  sensitive   = true
}
