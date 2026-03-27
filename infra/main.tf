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

module "lambda" {
  source = "./modules/lambda"

  lambda_role_arn = module.iam.lambda_role_arn
  project_name    = var.project_name
  environment     = var.environment
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