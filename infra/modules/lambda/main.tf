module "analyze" {
  source = "./dynamic_lambda"

  lambda_role_arn      = var.lambda_role_arn
  source_dir           = "${path.root}/../src/api/analyze"
  handler              = "handler.lambda_handler"
  lambda_function_name = "analyze-arch"
  runtime              = "python3.12"
  timeout              = 30
  layers = compact([
    var.common_layer_arn
  ])

  environment_variables = {
    ENVIRONMENT              = var.environment
    PROJECT_NAME             = var.project_name
    S3_DIAGRAM_BUCKET        = var.s3_diagram_bucket
    SQS_INGESTION_QUEUE_URL  = var.sqs_ingestion_queue_url
  }
}

