# Neo4j Module (Azure VM)

variable "environment" { type = string }
variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "subnet_id" { type = string }
variable "key_vault_id" { type = string }
variable "tags" { type = map(string) }

# Generate random password for Neo4j
resource "random_password" "neo4j_password" {
  length  = 32
  special = true
}

# Network Interface
resource "azurerm_network_interface" "neo4j" {
  name                = "nic-neo4j-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = var.subnet_id
    private_ip_address_allocation = "Dynamic"
  }

  tags = var.tags
}

# Network Security Group
resource "azurerm_network_security_group" "neo4j" {
  name                = "nsg-neo4j-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name

  security_rule {
    name                       = "Allow-Neo4j-Bolt"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "7687"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "Allow-Neo4j-HTTP"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "7474"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "*"
  }

  tags = var.tags
}

resource "azurerm_network_interface_security_group_association" "neo4j" {
  network_interface_id      = azurerm_network_interface.neo4j.id
  network_security_group_id = azurerm_network_security_group.neo4j.id
}

# Managed Disk for Data
resource "azurerm_managed_disk" "neo4j_data" {
  name                 = "disk-neo4j-data-${var.environment}"
  location             = var.location
  resource_group_name  = var.resource_group_name
  storage_account_type = var.environment == "prod" ? "Premium_LRS" : "Standard_LRS"
  create_option        = "Empty"
  disk_size_gb         = var.environment == "prod" ? 512 : 128

  tags = var.tags
}

# Virtual Machine
resource "azurerm_linux_virtual_machine" "neo4j" {
  name                = "vm-neo4j-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  size                = var.environment == "prod" ? "Standard_D4s_v3" : "Standard_D2s_v3"
  admin_username      = "neo4jadmin"

  network_interface_ids = [
    azurerm_network_interface.neo4j.id,
  ]

  admin_ssh_key {
    username   = "neo4jadmin"
    public_key = file("~/.ssh/id_rsa.pub")
  }

  os_disk {
    name                 = "disk-neo4j-os-${var.environment}"
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  identity {
    type = "SystemAssigned"
  }

  custom_data = base64encode(templatefile("${path.module}/neo4j-init.sh", {
    neo4j_password = random_password.neo4j_password.result
    environment    = var.environment
  }))

  tags = var.tags
}

# Attach data disk
resource "azurerm_virtual_machine_data_disk_attachment" "neo4j_data" {
  managed_disk_id    = azurerm_managed_disk.neo4j_data.id
  virtual_machine_id = azurerm_linux_virtual_machine.neo4j.id
  lun                = 0
  caching            = "ReadWrite"
}

output "vm_id" {
  value = azurerm_linux_virtual_machine.neo4j.id
}

output "private_ip" {
  value = azurerm_network_interface.neo4j.private_ip_address
}

output "connection_uri" {
  value = "bolt://${azurerm_network_interface.neo4j.private_ip_address}:7687"
}

output "bolt_url" {
  value = "bolt://${azurerm_network_interface.neo4j.private_ip_address}:7687"
}

output "http_url" {
  value = "http://${azurerm_network_interface.neo4j.private_ip_address}:7474"
}

output "admin_username" {
  value = "neo4j"
}

output "admin_password" {
  value     = random_password.neo4j_password.result
  sensitive = true
}
