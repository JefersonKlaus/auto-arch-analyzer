output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.ai_processor.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.ai_processor.arn
}

output "lambda_invoke_arn" {
  description = "Invoke ARN of the Lambda function"
  value       = aws_lambda_function.ai_processor.invoke_arn
}
