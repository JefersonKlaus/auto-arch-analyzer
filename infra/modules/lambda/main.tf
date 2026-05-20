module "analyze" {
  source = "./dynamic_lambda"

  lambda_role_arn      = var.lambda_role_arn
  source_dir           = "${path.root}/../src/api/post/diagram_analyze"
  handler              = "handler.lambda_handler"
  lambda_function_name = "analyze-arch"
  runtime              = "python3.12"
  timeout              = 30
  layers = compact([
    var.common_layer_arn
  ])

  environment_variables = {
    ENVIRONMENT             = var.environment
    PROJECT_NAME            = var.project_name
    S3_DIAGRAM_BUCKET       = var.s3_diagram_bucket
    SQS_INGESTION_QUEUE_URL = var.sqs_ingestion_queue_url
  }
}

module "file_validator" {
  source = "./dynamic_lambda"

  lambda_role_arn      = var.lambda_role_arn
  source_dir           = "${path.root}/../src/lambdas/file_validator"
  handler              = "handler.lambda_handler"
  lambda_function_name = "file-validator"
  runtime              = "python3.12"
  timeout              = 30
  layers = compact([
    var.common_layer_arn
  ])

  environment_variables = {
    ENVIRONMENT       = var.environment
    PROJECT_NAME      = var.project_name
    S3_DIAGRAM_BUCKET = var.s3_diagram_bucket
  }
}

module "ai_processor" {
  source = "./dynamic_lambda"

  lambda_role_arn      = var.lambda_role_arn
  source_dir           = "${path.root}/../src/lambdas/ai_processor"
  handler              = "handler.lambda_handler"
  lambda_function_name = "ai-processor"
  runtime              = "python3.12"
  timeout              = 30
  layers = compact([
    var.common_layer_arn
  ])

  environment_variables = {
    ENVIRONMENT       = var.environment
    PROJECT_NAME      = var.project_name
    S3_DIAGRAM_BUCKET = var.s3_diagram_bucket
  }
}

module "init_step_function" {
  source = "./dynamic_lambda"

  lambda_role_arn      = var.lambda_role_arn
  source_dir           = "${path.root}/../src/lambdas/init_step_function"
  handler              = "handler.lambda_handler"
  lambda_function_name = "init-step-function"
  runtime              = "python3.12"
  timeout              = 30
  layers = compact([
    var.common_layer_arn
  ])

  environment_variables = {
    ENVIRONMENT                    = var.environment
    PROJECT_NAME                   = var.project_name
    STEPFUNCTION_STATE_MACHINE_ARN = var.stepfunction_state_machine_arn
  }
}


module "report_adapter" {
  source = "./dynamic_lambda"

  lambda_role_arn      = var.lambda_role_arn
  source_dir           = "${path.root}/../src/lambdas/report_adapter"
  handler              = "handler.lambda_handler"
  lambda_function_name = "report-adapter"
  runtime              = "python3.12"
  timeout              = 30
  layers = compact([
    var.common_layer_arn
  ])

  environment_variables = {
    ENVIRONMENT            = var.environment
    PROJECT_NAME           = var.project_name
    DYNAMODB_TABLE_NAME    = var.dynamodb_table_name
    SQS_PDF_MAIL_QUEUE_URL = var.sqs_pdf_mail_queue_url
  }
}

module "pdf_mail_consumer" {
  source = "./dynamic_lambda"

  lambda_role_arn      = var.lambda_role_arn
  source_dir           = "${path.root}/../src/lambdas/pdf_mail_consumer"
  handler              = "handler.lambda_handler"
  lambda_function_name = "pdf-mail-consumer"
  runtime              = "python3.12"
  timeout              = 30
  layers = compact([
    var.common_layer_arn
  ])

  environment_variables = {
    ENVIRONMENT         = var.environment
    PROJECT_NAME        = var.project_name
    DYNAMODB_TABLE_NAME = var.dynamodb_table_name
  }
}

module "error_logger" {
  source = "./dynamic_lambda"

  lambda_role_arn      = var.lambda_role_arn
  source_dir           = "${path.root}/../src/lambdas/error_logger"
  handler              = "handler.lambda_handler"
  lambda_function_name = "error-logger"
  runtime              = "python3.12"
  timeout              = 30
  layers = compact([
    var.common_layer_arn
  ])

  environment_variables = {
    ENVIRONMENT  = var.environment
    PROJECT_NAME = var.project_name
  }
}

resource "aws_lambda_event_source_mapping" "init_step_function_sqs_trigger" {
  event_source_arn = var.sqs_ingestion_queue_arn
  function_name    = module.init_step_function.lambda_function_name
  batch_size       = 10
  enabled          = true
}

resource "aws_lambda_event_source_mapping" "pdf_mail_consumer_sqs_trigger" {
  event_source_arn = var.sqs_pdf_mail_queue_arn
  function_name    = module.pdf_mail_consumer.lambda_function_name
  batch_size       = 10
  enabled          = true
}
