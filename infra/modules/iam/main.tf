resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "LambdaAssumeRole"
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_s3_dynamodb" {
  name = "${var.project_name}-s3-dynamodb-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3ObjectAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [for bucket_arn in var.s3_bucket_arns : "${bucket_arn}/*"]
      },
      {
        Sid    = "S3BucketListAccess"
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = var.s3_bucket_arns
      },
      {
        Sid    = "DynamoDBReportsAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
        ]
        Resource = var.dynamodb_table_arn
      },
    ]
  })
}

resource "aws_iam_role_policy" "lambda_bedrock" {
  name = "${var.project_name}-bedrock-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid      = "BedrockInvokeModel"
      Effect   = "Allow"
      Action   = ["bedrock:InvokeModel"]
      Resource = "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.bedrock_model_id}"
      # Granting access to all Claude 3 models for flexibility.
      # This avoids access errors if the model ID in the code changes between Haiku, Sonnet, etc.
      Resource = "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-*"
    }]
  })
}

resource "aws_iam_role_policy" "sfn_lambda_invoke" {
  name = "${var.project_name}-sfn-lambda-invoke-policy"
  role = aws_iam_role.sfn_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid      = "AllowLambdaInvocation"
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = var.lambda_arns_for_sfn
    }]
  })
}

resource "aws_iam_role_policy" "lambda_marketplace" {
  name = "${var.project_name}-marketplace-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "MarketplaceSubscribe"
      Effect = "Allow"
      Action = [
        "aws-marketplace:ViewSubscriptions",
        "aws-marketplace:Subscribe"
      ]
      # These actions are not resource-specific in the same way as others
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy" "lambda_step_functions" {
  name = "${var.project_name}-step-functions-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid      = "StartWorkflowExecution"
      Effect   = "Allow"
      Action   = ["states:StartExecution"]
      Resource = var.stepfunction_state_machine_arn
    }]
  })
}

resource "aws_iam_role_policy" "lambda_sqs" {
  name = "${var.project_name}-sqs-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SQSSendMessage"
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueUrl",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          "arn:aws:sqs:${var.aws_region}:${var.aws_account_id}:${var.project_name}-*"
        ]
      },
      {
        Sid    = "SQSReceiveMessage"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          "arn:aws:sqs:${var.aws_region}:${var.aws_account_id}:${var.project_name}-*"
        ]
      }
    ]
  })
}

resource "aws_iam_role" "sfn_role" {
  name = "${var.project_name}-sfn-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "StepFunctionsAssumeRole"
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "states.amazonaws.com"
      }
    }]
  })
}
