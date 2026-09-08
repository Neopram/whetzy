# Cloudflare infrastructure — DNS records + Cloudflare Pages (frontend)

# ── Cloudflare Pages project (frontend SPA) ───────────────────────────────────

resource "cloudflare_pages_project" "frontend" {
  account_id        = var.cloudflare_account_id
  name              = "whetzy"
  production_branch = "master"

  build_config {
    build_command   = "npm run build"
    destination_dir = "dist"
    root_dir        = "frontend"
  }

  deployment_configs {
    production {
      environment_variables = {
        VITE_API_BASE_URL = "https://api-production-9751.up.railway.app"
        NODE_VERSION      = "20"
      }
    }
  }
}

# ── DNS records for whetzy.com ────────────────────────────────────────────────

# Apex: CNAME-equivalent via Cloudflare's "CNAME flattening" at the zone apex
resource "cloudflare_record" "apex" {
  zone_id = var.cloudflare_zone_id
  name    = "@"
  type    = "CNAME"
  value   = "${cloudflare_pages_project.frontend.name}.pages.dev"
  proxied = true
  ttl     = 1 # auto (proxied records ignore TTL)
}

# www subdomain → same Pages project
resource "cloudflare_record" "www" {
  zone_id = var.cloudflare_zone_id
  name    = "www"
  type    = "CNAME"
  value   = "${cloudflare_pages_project.frontend.name}.pages.dev"
  proxied = true
  ttl     = 1
}

# api subdomain → Railway backend (direct, not proxied so Railway's TLS is used)
resource "cloudflare_record" "api" {
  zone_id = var.cloudflare_zone_id
  name    = "api"
  type    = "CNAME"
  value   = "api-production-9751.up.railway.app"
  proxied = false
  ttl     = 300
}

# ── Custom domain on the Cloudflare Pages project ────────────────────────────

resource "cloudflare_pages_domain" "apex" {
  account_id   = var.cloudflare_account_id
  project_name = cloudflare_pages_project.frontend.name
  domain       = "whetzy.com"
  depends_on   = [cloudflare_record.apex]
}

resource "cloudflare_pages_domain" "www" {
  account_id   = var.cloudflare_account_id
  project_name = cloudflare_pages_project.frontend.name
  domain       = "www.whetzy.com"
  depends_on   = [cloudflare_record.www]
}

# ── Security headers via Cloudflare Transform Rule ────────────────────────────

resource "cloudflare_ruleset" "security_headers" {
  zone_id     = var.cloudflare_zone_id
  name        = "Whetzy security headers"
  description = "HSTS, CSP frame-ancestors, X-Content-Type-Options"
  kind        = "zone"
  phase       = "http_response_headers_transform"

  rules {
    action = "rewrite"
    action_parameters {
      headers {
        name      = "Strict-Transport-Security"
        operation = "set"
        value     = "max-age=31536000; includeSubDomains; preload"
      }
      headers {
        name      = "X-Content-Type-Options"
        operation = "set"
        value     = "nosniff"
      }
      headers {
        name      = "X-Frame-Options"
        operation = "set"
        value     = "DENY"
      }
      headers {
        name      = "Referrer-Policy"
        operation = "set"
        value     = "strict-origin-when-cross-origin"
      }
    }
    expression  = "true"
    description = "Global security headers"
    enabled     = true
  }
}
