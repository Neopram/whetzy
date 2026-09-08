terraform {
  required_version = ">= 1.6.0"

  required_providers {
    railway = {
      source  = "terraform-railway/railway"
      version = "~> 0.3"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }

  # Remote state on Terraform Cloud (free tier) — change bucket/workspace as needed.
  # To use local state instead, remove this block and run `terraform init`.
  backend "remote" {
    hostname     = "app.terraform.io"
    organization = "whetzy"
    workspaces {
      name = "whetzy-production"
    }
  }
}

provider "railway" {
  token = var.railway_token
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}
