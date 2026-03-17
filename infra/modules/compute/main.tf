resource "aws_cloudwatch_log_group" "ai_processor" {
  name              = "/aws/lambda/${var.project_name}-ai-processor"
  retention_in_days = var.log_retention_days
}

resource "aws_lambda_function" "ai_processor" {
  function_name = "${var.project_name}-ai-processor"
  role          = var.lambda_role_arn
  handler       = "adapter.handler"
  runtime       = "python3.12"
  filename      = "ai_processor.zip"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  environment {
    variables = {
      S3_BUCKET  = var.s3_bucket_id
      TABLE_NAME = var.dynamodb_table_name
    }
  }

  depends_on = [aws_cloudwatch_log_group.ai_processor]
}
