# Railway infrastructure — backend service + environment variables
#
# Railway does not expose DB/Redis provisioning through its Terraform provider
# (as of v0.3). Those are created manually in the Railway dashboard or via
# the Railway CLI and referenced here by their connection string variables.
#
# To deploy a new environment from scratch:
#   1. `railway init` in the repo root → creates project + environment
#   2. Add PostgreSQL + Redis plugins via the Railway dashboard
#   3. Fill in terraform.tfvars with the resulting IDs and connection strings
#   4. `terraform apply` to sync all env vars and deploy the backend service

# ── Environment variables on the production backend service ──────────────────

resource "railway_variable" "environment" {
  project_id     = var.railway_project_id
  environment_id = var.railway_environment_id
  name           = "ENVIRONMENT"
  value          = "production"
}

resource "railway_variable" "secret_key" {
  project_id     = var.railway_project_id
  environment_id = var.railway_environment_id
  name           = "SECRET_KEY"
  value          = var.secret_key
}

resource "railway_variable" "groq_api_key" {
  project_id     = var.railway_project_id
  environment_id = var.railway_environment_id
  name           = "GROQ_API_KEY"
  value          = var.groq_api_key
}

resource "railway_variable" "stripe_secret_key" {
  project_id     = var.railway_project_id
  environment_id = var.railway_environment_id
  name           = "STRIPE_SECRET_KEY"
  value          = var.stripe_secret_key
}

resource "railway_variable" "stripe_webhook_secret" {
  project_id     = var.railway_project_id
  environment_id = var.railway_environment_id
  name           = "STRIPE_WEBHOOK_SECRET"
  value          = var.stripe_webhook_secret
}

resource "railway_variable" "stripe_price_plus" {
  project_id     = var.railway_project_id
  environment_id = var.railway_environment_id
  name           = "STRIPE_PRICE_PLUS"
  value          = var.stripe_price_plus
}

resource "railway_variable" "content_admin_key" {
  project_id     = var.railway_project_id
  environment_id = var.railway_environment_id
  name           = "CONTENT_ADMIN_KEY"
  value          = var.content_admin_key
}

resource "railway_variable" "sentry_dsn" {
  project_id     = var.railway_project_id
  environment_id = var.railway_environment_id
  name           = "SENTRY_DSN"
  value          = var.sentry_dsn
}

resource "railway_variable" "vapid_private_key" {
  project_id     = var.railway_project_id
  environment_id = var.railway_environment_id
  name           = "VAPID_PRIVATE_KEY"
  value          = var.vapid_private_key
}

resource "railway_variable" "vapid_public_key" {
  project_id     = var.railway_project_id
  environment_id = var.railway_environment_id
  name           = "VAPID_PUBLIC_KEY"
  value          = var.vapid_public_key
}

resource "railway_variable" "trust_proxy_headers" {
  project_id     = var.railway_project_id
  environment_id = var.railway_environment_id
  name           = "TRUST_PROXY_HEADERS"
  value          = "true"
}

resource "railway_variable" "debug" {
  project_id     = var.railway_project_id
  environment_id = var.railway_environment_id
  name           = "DEBUG"
  value          = "false"
}
