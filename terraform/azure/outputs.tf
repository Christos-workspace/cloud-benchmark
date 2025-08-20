output "resource_group_name" {
  description = "The name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "storage_account_name" {
  description = "The name of the Azure Storage Account"
  value       = azurerm_storage_account.main.name
}

output "storage_account_connection_string" {
  description = "Primary connection string for the storage account"
  value       = azurerm_storage_account.main.primary_connection_string
  sensitive   = true
}

output "blob_container_name" {
  description = "The name of the results blob container"
  value       = azurerm_storage_container.results.name
}

output "container_group_name" {
  description = "The name of the Azure Container Instance group"
  value       = length(azurerm_container_group.scraper) > 0 ? azurerm_container_group.scraper[0].name : ""
}

output "container_group_ip_address" {
  description = "The public IP address of the Azure Container Instance group"
  value       = length(azurerm_container_group.scraper) > 0 ? azurerm_container_group.scraper[0].ip_address : ""
}

output "acr_login_server" {
  description = "The login server of the Azure Container Registry"
  value       = azurerm_container_registry.acr.login_server
}

output "acr_admin_username" {
  description = "The admin username for the Azure Container Registry"
  value       = azurerm_container_registry.acr.admin_username
}

output "acr_admin_password" {
  description = "The admin password for the Azure Container Registry"
  value       = azurerm_container_registry.acr.admin_password
  sensitive   = true
}
