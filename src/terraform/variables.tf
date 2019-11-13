variable app_version {
  type        = string
  description = "Current version"
  default     = "1-0-1"
}

variable project_id {
  type        = string
  description = "The project ID to manage the Cloud SQL resources"
  default     = "agrc-sgid-development-83912828"
}

variable name {
  type        = string
  description = "The name of the Cloud SQL resources"
  default     = "public-sgid"
}

variable database_version {
  type        = string
  description = "The database version to use"
  default     = "POSTGRES_11"
}

variable region {
  type        = string
  description = "The region of the Cloud SQL resources"
  default     = "us-west2"
}

variable tier {
  type        = string
  description = "The tier for the master instance."
  default     = "db-custom-1-3840"
}

variable disk_autoresize {
  type        = bool
  description = "Configuration to increase storage size."
  default     = true
}

variable disk_size {
  type        = number
  description = "The disk size for the master instance."
  default     = 20
}

variable disk_type {
  type        = string
  description = "The disk type for the master instance."
  default     = "PD_SSD"
}

variable pricing_plan {
  type        = string
  description = "The pricing plan for the master instance."
  default     = "PER_USE"
}

variable maintenance_window_day {
  type        = number
  description = "he day of week (1-7) for the master instance maintenance."
  default     = 7
}

variable maintenance_window_hour {
  type        = number
  description = "The hour of day (0-23) maintenance window for the master instance maintenance."
  default     = 7
}

variable maintenance_window_update_track {
  type        = string
  description = "The update track of maintenance window for the master instance maintenance.Can be either `canary` or `stable`."
  default     = "stable"
}

variable user_labels {
  description = "The standard DTS labels for billing"
  type        = map(string)
  default = {
    app        = "public-sgid"
    supportcod = "tbd"
    elcid      = "itagrc"
    contact    = "steve-gourley"
    dept       = "agr"
    env        = "prod"
    security   = "tbd"
  }
}

variable ip_configuration {
  description = "The ip configuration for the master instances."
  type = object({
    authorized_networks = list(map(string))
    ipv4_enabled        = bool
    private_network     = string
    require_ssl         = bool
  })
  default = {
    authorized_networks = [{
      name = "public"
      cidr = "0.0.0.0/0"
    }]
    ipv4_enabled    = true
    private_network = null
    require_ssl     = null
  }
}

variable db_name {
  type        = string
  description = "Name of the default database to create"
  default     = "cloud"
}

variable user_name {
  type        = string
  description = "The name of the default user"
  default     = "dba"
}
