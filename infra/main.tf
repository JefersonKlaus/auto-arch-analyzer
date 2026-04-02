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

  project_name   = var.project_name
  aws_account_id = var.aws_account_id
  aws_region     = var.aws_region
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

  lambda_role_arn         = module.iam.lambda_role_arn
  project_name            = var.project_name
  environment             = var.environment
  s3_diagram_bucket       = module.s3.diagram_upload_bucket_name
  sqs_ingestion_queue_url = module.queue.ingestion_queue_url
  common_layer_arn        = module.layers.common_layer_arn
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