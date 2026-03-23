output "api_url" {
  value = "${var.rest_api_id}/${var.path_part}"
}

output "resource_id" {
  value = aws_api_gateway_resource.api_resource.id
}

