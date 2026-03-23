output "hello_world_function_arn" {
  description = "ARN of the Hello World Lambda function"
  value       = module.hello_world.lambda_function_arn
}

output "hello_world_function_name" {
  description = "Name of the Hello World Lambda function"
  value       = module.hello_world.lambda_function_name
}
