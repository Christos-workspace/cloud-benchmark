# Use a random_id to generate a unique storage account suffix
resource "random_id" "storage_suffix" {
  byte_length = 2 # 2 bytes = 4 hex chars, e.g. "a1b2"
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
}

# Storage Account
resource "azurerm_storage_account" "main" {
  name                     = lower("${var.storage_account_prefix}${random_id.storage_suffix.hex}")
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  allow_blob_public_access = false

  depends_on = [azurerm_resource_group.main]
}

# Storage Container (for results)
resource "azurerm_storage_container" "results" {
  name                  = var.blob_container_name
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Azure Container Instance (runs your Docker image)
resource "azurerm_container_group" "scraper" {
  name                = var.container_group_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"

  container {
    name   = "scraper"
    image  = var.docker_image
    cpu    = 1
    memory = 1.5

    environment_variables = {
      AZURE_BLOB_CONTAINER            = azurerm_storage_container.results.name
      AZURE_STORAGE_CONNECTION_STRING = azurerm_storage_account.main.primary_connection_string
    }
  }

  ip_address_type = "public"
}
