# ==============================================================================
# provider.tf
# Configures the Azure provider to allow Terraform resource provisioning.
# Credentials are provided via Airflow DAG at runtime.
# ==============================================================================

provider "azurerm" {
  features {}
  client_id       = var.client_id
  client_secret   = var.client_secret
  tenant_id       = var.tenant_id
  subscription_id = var.subscription_id
}
