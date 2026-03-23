output "hello_world_function_arn" {
  description = "ARN of the Hello World Lambda function"
  value       = module.hello_world.lambda_function_arn
}

output "hello_world_function_name" {
  description = "Name of the Hello World Lambda function"
  value       = module.hello_world.lambda_function_name
}

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
