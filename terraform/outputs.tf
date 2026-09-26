output "vpc_id" {
  description = "The ID of the RakshakGIS VPC."
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "The ID of the public subnet hosting the application."
  value       = aws_subnet.public.id
}

output "security_group_id" {
  description = "The ID of the application security group."
  value       = aws_security_group.app.id
}

output "instance_id" {
  description = "The EC2 instance ID."
  value       = aws_instance.app.id
}

output "public_ip" {
  description = "The static public Elastic IP (or public IP) of the RakshakGIS server."
  value       = var.allocate_elastic_ip ? aws_eip.app[0].public_ip : aws_instance.app.public_ip
}

output "ssh_connection_string" {
  description = "Example SSH command to connect to the instance."
  value       = "ssh -i <your-key.pem> ubuntu@${var.allocate_elastic_ip ? aws_eip.app[0].public_ip : aws_instance.app.public_ip}"
}

output "frontend_url" {
  description = "Public URL to access the RakshakGIS Next.js frontend application."
  value       = "http://${var.allocate_elastic_ip ? aws_eip.app[0].public_ip : aws_instance.app.public_ip}:3000"
}

output "backend_api_url" {
  description = "Public URL for the FastAPI backend API."
  value       = "http://${var.allocate_elastic_ip ? aws_eip.app[0].public_ip : aws_instance.app.public_ip}:8000/api/v1"
}

output "backend_health_url" {
  description = "Public URL for the backend health check probe."
  value       = "http://${var.allocate_elastic_ip ? aws_eip.app[0].public_ip : aws_instance.app.public_ip}:8000/health"
}

output "database_isolation_note" {
  description = "Security posture notice regarding database accessibility."
  value       = "SECURITY GUARANTEE: PostgreSQL port 5432 is intentionally unexposed to the Internet. Manage the database via SSH: ssh ubuntu@<public_ip> 'docker exec -it rakshakgis-prod-db psql -U rakshak -d rakshakgis'"
}
