output instance_name {
  value       = google_sql_database_instance.public_sgid.name
  description = "The instance name for the master instance"
}

output db_name {
  value       = google_sql_database.public_sgid.name
  description = "The default database name"
}

output instance_first_ip_address {
  value       = google_sql_database_instance.public_sgid.first_ip_address
  description = "The first IPv4 address of the addresses assigned."
}

output dbo_password {
  value       = google_sql_user.dbo.password
  description = "The postgres database owner password"
}
