# Azure region for all resources
variable "location" {
  description = "The Azure region to deploy resources into"
  type        = string
  default     = "francecentral"
}

# Resource group name
variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
}

# Storage account prefix (must be lowercase, 3-18 chars to allow for suffix)
variable "storage_account_prefix" {
  description = "The prefix for the storage account name (must be lowercase, 3-18 chars)"
  type        = string
  default     = "cloudbench"
}

# Blob container name
variable "blob_container_name" {
  description = "The name of the blob container for results"
  type        = string
}

# Container group name (for Azure Container Instance)
variable "container_group_name" {
  description = "The name of the Azure Container Instance group"
  type        = string
}

# Docker image to run
variable "docker_image" {
  description = "The Docker image to run in Azure Container Instance"
  type        = string
}
