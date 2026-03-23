module "hello_world" {
  source = "./dynamic_lambda"

  lambda_role_arn      = var.lambda_role_arn
  source_dir           = "${path.root}/../src/api/hello_world"
  handler              = "handler.lambda_handler"
  lambda_function_name = "${var.project_name}-hello-world"
  runtime              = "python3.12"

  environment_variables = {
    ENVIRONMENT = var.environment
  }
}
