variable "railway_token" {
  description = "Railway API token (from railway.app → Account Settings → Tokens)."
  type        = string
  sensitive   = true
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token with Zone:Edit + Pages:Edit permissions."
  type        = string
  sensitive   = true
}

variable "cloudflare_account_id" {
  description = "Cloudflare account ID (shown in right sidebar of the dashboard)."
  type        = string
}

variable "cloudflare_zone_id" {
  description = "Cloudflare Zone ID for whetzy.com."
  type        = string
}

variable "railway_project_id" {
  description = "Existing Railway project ID (from project URL: railway.app/project/<id>)."
  type        = string
}

variable "railway_environment_id" {
  description = "Railway environment ID for the production environment."
  type        = string
}

# --- Secrets forwarded to Railway services ---
variable "secret_key" {
  description = "Django-style SECRET_KEY for JWT signing."
  type        = string
  sensitive   = true
}

variable "groq_api_key" {
  description = "Groq API key for AI completions."
  type        = string
  sensitive   = true
  default     = ""
}

variable "stripe_secret_key" {
  description = "Stripe secret key (sk_live_...)."
  type        = string
  sensitive   = true
  default     = ""
}

variable "stripe_webhook_secret" {
  description = "Stripe webhook signing secret (whsec_...)."
  type        = string
  sensitive   = true
  default     = ""
}

variable "stripe_price_plus" {
  description = "Stripe price ID for the Plus plan."
  type        = string
  default     = ""
}

variable "content_admin_key" {
  description = "X-Admin-Key value for content management endpoints."
  type        = string
  sensitive   = true
  default     = ""
}

variable "sentry_dsn" {
  description = "Sentry DSN for error tracking (leave empty to disable)."
  type        = string
  sensitive   = true
  default     = ""
}

variable "vapid_private_key" {
  description = "VAPID private key for web push notifications."
  type        = string
  sensitive   = true
  default     = ""
}

variable "vapid_public_key" {
  description = "VAPID public key for web push notifications."
  type        = string
  default     = ""
}
