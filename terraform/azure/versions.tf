# ==============================================================================
# versions.tf
# Specifies required Terraform and provider versions for reproducibility.
# ==============================================================================

terraform {
  required_version = ">= 1.2.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.88"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}
