output "common_layer_arn" {
  description = "ARN of the common lambda layer"
  value       = aws_lambda_layer_version.common_layer.arn
}
