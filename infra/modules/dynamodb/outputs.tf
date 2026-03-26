output "table_name" {
  description = "Name of the project DynamoDB single table"
  value       = aws_dynamodb_table.project_table.name
}

output "table_arn" {
  description = "ARN of the project DynamoDB single table"
  value       = aws_dynamodb_table.project_table.arn
}
