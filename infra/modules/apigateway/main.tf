// API REST publica com endpoint /analyze para receber requisicoes assincronas.
resource "aws_api_gateway_rest_api" "analyzer_api" {
  name        = "${var.project_name}-api"
  description = "API Gateway for async architecture analysis ingestion"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

// Recurso unico da API: /analyze com metodo POST e CORS via modulo dinamico.
module "analyze_resource" {
  source      = "./dynamic_apigateway"
  rest_api_id = aws_api_gateway_rest_api.analyzer_api.id
  parent_id   = aws_api_gateway_rest_api.analyzer_api.root_resource_id
  path_full   = "diagram-analyze"
  path_part   = "diagram-analyze"

  http_methods = ["POST"]
  lambda_function_names = {
    POST = "analyze-arch"
  }

  region             = var.aws_region
  account_id         = var.aws_account_id
  enable_cors        = true
}
