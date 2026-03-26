output "analyze_function_arn" {
  description = "ARN of the Analyze Lambda function"
  value       = module.analyze.lambda_function_arn
}

output "analyze_function_name" {
  description = "Name of the Analyze Lambda function"
  value       = module.analyze.lambda_function_name
}

output "analyze_function_invoke_arn" {
  description = "Invoke ARN of the Analyze Lambda function"
  value       = module.analyze.lambda_function_invoke_arn
}
