terraform {
  backend "s3" {}
}

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    Company     = "FIAP Secure Systems"
    Course      = "SOAT-IADT"
    ManagedBy   = "Terraform"
  }

  # Keep deterministic ARN to avoid module dependency cycle.
  step_functions_workflow_arn = "arn:aws:states:${var.aws_region}:${var.aws_account_id}:stateMachine:${var.project_name}-workflow"
}

module "s3" {
  source = "./modules/s3"

  project_name = var.project_name
  environment  = var.environment
  tags         = local.common_tags
}

module "dynamodb" {
  source = "./modules/dynamodb"

  project_name = var.project_name
  tags         = local.common_tags
}

module "iam" {
  source = "./modules/iam"

  project_name                   = var.project_name
  aws_account_id                 = var.aws_account_id
  aws_region                     = var.aws_region
  stepfunction_state_machine_arn = local.step_functions_workflow_arn
  s3_bucket_arns = [
    module.s3.diagram_upload_bucket_arn,
    module.s3.analysis_result_bucket_arn,
    module.s3.freeze_bucket_arn,
  ]
  dynamodb_table_arn = module.dynamodb.table_arn
}

module "layers" {
  source = "./modules/layers"

  project_name = var.project_name
  environment  = var.environment
}


module "lambda" {
  source = "./modules/lambda"

  lambda_role_arn                = module.iam.lambda_role_arn
  project_name                   = var.project_name
  environment                    = var.environment
  s3_diagram_bucket              = module.s3.diagram_upload_bucket_name
  sqs_ingestion_queue_url        = module.queue.ingestion_queue_url
  sqs_ingestion_queue_arn        = module.queue.ingestion_queue_arn
  stepfunction_state_machine_arn = local.step_functions_workflow_arn
  common_layer_arn               = module.layers.common_layer_arn
  dynamodb_table_name            = module.dynamodb.table_name
  sqs_pdf_mail_queue_url         = module.queue.pdf_mail_queue_url
}

module "queue" {
  source = "./modules/queue"

  project_name = var.project_name
}

module "api_gateway" {
  source = "./modules/apigateway"

  project_name   = var.project_name
  environment    = var.environment
  aws_region     = var.aws_region
  aws_account_id = var.aws_account_id
}

module "orchestration" {
  source = "./modules/orchestration"

  project_name              = var.project_name
  sfn_role_arn              = module.iam.sfn_role_arn
  sfn_role_id               = module.iam.sfn_role_id
  file_validator_lambda_arn = module.lambda.file_validator_function_arn
  ai_processor_lambda_arn   = module.lambda.ai_processor_function_arn
  report_adapter_lambda_arn = module.lambda.report_adapter_function_arn
  error_logger_lambda_arn   = module.lambda.error_logger_function_arn
}
