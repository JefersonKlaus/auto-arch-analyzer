output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_role.arn
}

output "sfn_role_arn" {
  description = "ARN of the Step Functions role"
  value       = aws_iam_role.sfn_role.arn
}

output "sfn_role_id" {
  description = "ID of the Step Functions role"
  value       = aws_iam_role.sfn_role.id
}
