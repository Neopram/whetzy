output "pages_url" {
  description = "Cloudflare Pages deployment URL (*.pages.dev)"
  value       = "https://${cloudflare_pages_project.frontend.name}.pages.dev"
}

output "railway_project_id" {
  description = "Railway project ID (useful for CI environment variables)"
  value       = var.railway_project_id
}
