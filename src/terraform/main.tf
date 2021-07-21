locals {
  ip_configuration_enabled = length(keys(var.ip_configuration)) > 0 ? true : false

  ip_configurations = {
    enabled  = var.ip_configuration
    disabled = {}
  }
}

provider "google" {
  credentials = file("terraform-sa.json")
  project     = var.project_id
}

resource "google_sql_database_instance" "public_sgid" {
  name             = "${var.name}-v${var.app_version}"
  project          = var.project_id
  region           = var.region
  database_version = var.database_version

  settings {
    tier            = var.tier
    disk_type       = var.disk_type
    disk_size       = var.disk_size
    disk_autoresize = var.disk_autoresize
    pricing_plan    = var.pricing_plan
    user_labels     = var.user_labels
    dynamic "ip_configuration" {
      for_each = [local.ip_configurations[local.ip_configuration_enabled ? "enabled" : "disabled"]]
      content {
        ipv4_enabled    = lookup(ip_configuration.value, "ipv4_enabled", null)
        private_network = lookup(ip_configuration.value, "private_network", null)
        require_ssl     = lookup(ip_configuration.value, "require_ssl", null)

        dynamic "authorized_networks" {
          for_each = lookup(ip_configuration.value, "authorized_networks", [])
          content {
            expiration_time = lookup(authorized_networks.value, "expiration_time", null)
            name            = lookup(authorized_networks.value, "name", null)
            value           = lookup(authorized_networks.value, "cidr", null)
          }
        }
      }
    }
    maintenance_window {
      day          = var.maintenance_window_day
      hour         = var.maintenance_window_hour
      update_track = var.maintenance_window_update_track
    }
  }
}

resource "google_sql_database" "public_sgid" {
  name     = var.db_name
  project  = var.project_id
  instance = google_sql_database_instance.public_sgid.name
  depends_on = [google_sql_database_instance.public_sgid]
}

resource "random_id" "dbo_password" {
  keepers = {
    name = google_sql_database_instance.public_sgid.name
  }

  byte_length = 25
}

resource "google_sql_user" "dbo" {
  name       = "postgres"
  project    = var.project_id
  instance   = google_sql_database_instance.public_sgid.name
  password   = sensitive(random_id.dbo_password.hex)
  depends_on = [google_sql_database_instance.public_sgid, random_id.dbo_password]
}
