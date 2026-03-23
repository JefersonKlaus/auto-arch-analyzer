resource "aws_api_gateway_resource" "api_resource" {
  rest_api_id = var.rest_api_id
  parent_id   = var.parent_id
  path_part   = var.path_part
}

resource "aws_api_gateway_method" "api_method" {
  for_each      = toset(var.http_methods)
  rest_api_id   = var.rest_api_id
  resource_id   = aws_api_gateway_resource.api_resource.id
  http_method   = each.value
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = var.authorizer_id
}

resource "aws_api_gateway_integration" "api_integration" {
  for_each                = toset(var.http_methods)
  rest_api_id             = var.rest_api_id
  resource_id             = aws_api_gateway_resource.api_resource.id
  http_method             = aws_api_gateway_method.api_method[each.value].http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/arn:aws:lambda:${var.region}:${var.account_id}:function:${var.lambda_function_names[each.value]}/invocations"
  timeout_milliseconds    = var.integration_timeout_milliseconds
}

resource "aws_lambda_permission" "lambda_permission" {
  for_each      = toset(var.http_methods)
  statement_id  = "AllowAPIGatewayInvoke-${each.value}"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_names[each.value]
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${var.region}:${var.account_id}:${var.rest_api_id}/*/${each.value}/${var.path_full}"
  depends_on    = [aws_api_gateway_resource.api_resource]
}

resource "aws_api_gateway_method_response" "api_method_response" {
  for_each    = toset(var.http_methods)
  rest_api_id = var.rest_api_id
  resource_id = aws_api_gateway_resource.api_resource.id
  http_method = aws_api_gateway_method.api_method[each.value].http_method
  status_code = "200"

  response_parameters = var.enable_cors ? {
    "method.response.header.Access-Control-Allow-Origin" = true
  } : {}
}

resource "aws_api_gateway_integration_response" "api_integration_response" {
  for_each    = var.enable_cors ? toset(var.http_methods) : []
  rest_api_id = var.rest_api_id
  resource_id = aws_api_gateway_resource.api_resource.id
  http_method = aws_api_gateway_method.api_method[each.value].http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [
    aws_api_gateway_integration.api_integration,
    aws_api_gateway_method_response.api_method_response
  ]
}

resource "aws_api_gateway_method" "cors_options" {
  count         = var.enable_cors ? 1 : 0
  rest_api_id   = var.rest_api_id
  resource_id   = aws_api_gateway_resource.api_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "cors_integration" {
  count       = var.enable_cors ? 1 : 0
  rest_api_id = var.rest_api_id
  resource_id = aws_api_gateway_resource.api_resource.id
  http_method = aws_api_gateway_method.cors_options[0].http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
  passthrough_behavior = "WHEN_NO_MATCH"
}

resource "aws_api_gateway_method_response" "cors_method_response" {
  count       = var.enable_cors ? 1 : 0
  rest_api_id = var.rest_api_id
  resource_id = aws_api_gateway_resource.api_resource.id
  http_method = aws_api_gateway_method.cors_options[0].http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Headers" = true
  }
}

resource "aws_api_gateway_integration_response" "cors_integration_response" {
  count       = var.enable_cors ? 1 : 0
  rest_api_id = var.rest_api_id
  resource_id = aws_api_gateway_resource.api_resource.id
  http_method = aws_api_gateway_method.cors_options[0].http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'",
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,OPTIONS'",
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
  }

  depends_on = [
    aws_api_gateway_integration.cors_integration,
    aws_api_gateway_method_response.cors_method_response
  ]
}
