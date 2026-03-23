terraform {
  backend "s3" {}
}

locals {
  project_name = var.project_name
  common_tags = {
    Project     = "HACKATHON-FIAP"
    Environment = var.environment
    Company     = "FIAP Secure Systems"
    Course      = "SOAT-IADT"
    ManagedBy   = "Terraform"
  }
}

module "storage" {
  source = "./modules/storage"

  project_name = local.project_name
}

module "iam" {
  source = "./modules/iam"

  project_name       = local.project_name
  aws_account_id     = var.aws_account_id
  aws_region         = var.aws_region
  s3_bucket_arn      = module.storage.s3_bucket_arn
  dynamodb_table_arn = module.storage.dynamodb_table_arn
}

module "lambda" {
  source = "./modules/lambda"

  lambda_role_arn = module.iam.lambda_role_arn
  project_name    = local.project_name
  environment     = var.environment
}

module "queue" {
  source = "./modules/queue"

  project_name = local.project_name
}

module "api_gateway" {
  source = "./modules/apigateway"

  project_name                 = local.project_name
  environment                  = var.environment
  aws_region                   = var.aws_region
  aws_account_id               = var.aws_account_id
  ingestion_queue_name         = module.queue.ingestion_queue_name
  ingestion_queue_arn          = module.queue.ingestion_queue_arn
  analyze_lambda_function_name = module.lambda.analyze_function_name
}

# module "compute" {
#   source = "./modules/compute"

#   project_name        = local.project_name
#   log_retention_days  = var.log_retention_days
#   lambda_timeout      = var.lambda_timeout
#   lambda_memory_size  = var.lambda_memory_size
#   lambda_role_arn     = module.iam.lambda_role_arn
#   s3_bucket_id        = module.storage.s3_bucket_id
#   dynamodb_table_name = module.storage.dynamodb_table_name
# }

# module "network" {
#   source = "./modules/network"

#   project_name         = local.project_name
#   environment          = var.environment
#   lambda_invoke_arn    = module.compute.lambda_invoke_arn
#   lambda_function_name = module.compute.lambda_function_name
# }

# module "orchestration" {
#   source = "./modules/orchestration"

#   project_name        = local.project_name
#   sfn_role_arn        = module.iam.sfn_role_arn
#   sfn_role_id         = module.iam.sfn_role_id
#   lambda_function_arn = module.compute.lambda_function_arn
# }