// Permite que o API Gateway assuma uma role IAM para publicar mensagens no SQS.
data "aws_iam_policy_document" "apigateway_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "apigateway_sqs_role" {
  name               = "${var.project_name}-apigateway-sqs-role"
  assume_role_policy = data.aws_iam_policy_document.apigateway_assume_role.json
}

// Politica minima para enviar mensagens na fila de ingestao.
data "aws_iam_policy_document" "apigateway_sqs_policy" {
  statement {
    effect = "Allow"
    actions = [
      "sqs:SendMessage",
      "sqs:GetQueueUrl",
      "sqs:GetQueueAttributes",
    ]
    resources = [var.ingestion_queue_arn]
  }
}

resource "aws_iam_role_policy" "apigateway_sqs_policy" {
  name   = "${var.project_name}-apigateway-sqs-policy"
  role   = aws_iam_role.apigateway_sqs_role.id
  policy = data.aws_iam_policy_document.apigateway_sqs_policy.json
}

// API REST publica com endpoint /analyze para receber requisicoes assincronas.
resource "aws_api_gateway_rest_api" "analyzer_api" {
  name        = "${var.project_name}-api"
  description = "API Gateway for async architecture analysis ingestion"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_resource" "analyze" {
  rest_api_id = aws_api_gateway_rest_api.analyzer_api.id
  parent_id   = aws_api_gateway_rest_api.analyzer_api.root_resource_id
  path_part   = "analyze"
}

resource "aws_api_gateway_method" "analyze_post" {
  rest_api_id   = aws_api_gateway_rest_api.analyzer_api.id
  resource_id   = aws_api_gateway_resource.analyze.id
  http_method   = "POST"
  authorization = "NONE"
}

// Integra o POST /analyze diretamente com SQS (sem Lambda), montando o payload via VTL.
resource "aws_api_gateway_integration" "analyze_post_sqs" {
  rest_api_id             = aws_api_gateway_rest_api.analyzer_api.id
  resource_id             = aws_api_gateway_resource.analyze.id
  http_method             = aws_api_gateway_method.analyze_post.http_method
  integration_http_method = "POST"
  type                    = "AWS"
  credentials             = aws_iam_role.apigateway_sqs_role.arn
  passthrough_behavior    = "NEVER"
  uri                     = "arn:aws:apigateway:${var.aws_region}:sqs:path/${var.aws_account_id}/${var.ingestion_queue_name}"

  request_parameters = {
    "integration.request.header.Content-Type" = "'application/x-www-form-urlencoded'"
  }

  request_templates = {
    "application/json" = <<-EOT
Action=SendMessage&MessageBody=$util.urlEncode("{\"request_id\":\"$context.requestId\",\"received_at\":\"$context.requestTimeEpoch\",\"email\":\"$util.escapeJavaScript($input.path('$.email'))\",\"prompt\":\"$util.escapeJavaScript($input.path('$.prompt'))\",\"diagram\":\"$util.escapeJavaScript($input.path('$.diagram'))\",\"status\":\"QUEUED\"}")
EOT
  }

  depends_on = [aws_iam_role_policy.apigateway_sqs_policy]
}

// Resposta de sucesso do endpoint de ingestao: retorna 202 Accepted para processamento async.
resource "aws_api_gateway_method_response" "analyze_post_202" {
  rest_api_id = aws_api_gateway_rest_api.analyzer_api.id
  resource_id = aws_api_gateway_resource.analyze.id
  http_method = aws_api_gateway_method.analyze_post.http_method
  status_code = "202"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
    "method.response.header.Content-Type"                = true
  }
}

resource "aws_api_gateway_integration_response" "analyze_post_202" {
  rest_api_id = aws_api_gateway_rest_api.analyzer_api.id
  resource_id = aws_api_gateway_resource.analyze.id
  http_method = aws_api_gateway_method.analyze_post.http_method
  status_code = aws_api_gateway_method_response.analyze_post_202.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
    "method.response.header.Content-Type"                = "'application/json'"
  }

  response_templates = {
    "application/json" = <<-EOT
{"message":"Request accepted for processing","execution_id":"$context.requestId","status":"QUEUED","timestamp":"$context.requestTime"}
EOT
  }

  depends_on = [aws_api_gateway_integration.analyze_post_sqs]
}

// Endpoint OPTIONS para CORS no recurso /analyze.
resource "aws_api_gateway_method" "analyze_options" {
  rest_api_id   = aws_api_gateway_rest_api.analyzer_api.id
  resource_id   = aws_api_gateway_resource.analyze.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "analyze_options" {
  rest_api_id = aws_api_gateway_rest_api.analyzer_api.id
  resource_id = aws_api_gateway_resource.analyze.id
  http_method = aws_api_gateway_method.analyze_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "analyze_options_200" {
  rest_api_id = aws_api_gateway_rest_api.analyzer_api.id
  resource_id = aws_api_gateway_resource.analyze.id
  http_method = aws_api_gateway_method.analyze_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Headers" = true
  }
}

resource "aws_api_gateway_integration_response" "analyze_options_200" {
  rest_api_id = aws_api_gateway_rest_api.analyzer_api.id
  resource_id = aws_api_gateway_resource.analyze.id
  http_method = aws_api_gateway_method.analyze_options.http_method
  status_code = aws_api_gateway_method_response.analyze_options_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,POST'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
  }

  depends_on = [aws_api_gateway_integration.analyze_options]
}

// Forca novo deployment quando metodo/integracao mudam, mantendo stage estavel.
resource "aws_api_gateway_deployment" "analyzer" {
  rest_api_id = aws_api_gateway_rest_api.analyzer_api.id

  triggers = {
    redeployment = sha1(jsonencode({
      analyze_method      = aws_api_gateway_method.analyze_post.id
      analyze_integration = aws_api_gateway_integration.analyze_post_sqs.id
      options_method      = aws_api_gateway_method.analyze_options.id
    }))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration_response.analyze_post_202,
    aws_api_gateway_integration_response.analyze_options_200,
  ]
}

resource "aws_api_gateway_stage" "analyzer" {
  rest_api_id   = aws_api_gateway_rest_api.analyzer_api.id
  deployment_id = aws_api_gateway_deployment.analyzer.id
  stage_name    = var.environment
}