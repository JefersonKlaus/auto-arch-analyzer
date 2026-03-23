output "api_gateway_id" {
  description = "ID of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.analyzer_api.id
}

output "api_gateway_invoke_url" {
  description = "Base invoke URL of the deployed API stage"
  value       = "https://${aws_api_gateway_rest_api.analyzer_api.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_api_gateway_stage.analyzer.stage_name}"
}

output "analyze_endpoint_url" {
  description = "Full URL for POST /analyze"
  value       = "https://${aws_api_gateway_rest_api.analyzer_api.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_api_gateway_stage.analyzer.stage_name}/analyze"
}
