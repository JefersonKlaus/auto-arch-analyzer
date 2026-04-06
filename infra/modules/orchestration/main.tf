resource "aws_iam_role_policy" "sfn_invoke_lambda" {
  name = "${var.project_name}-sfn-invoke-lambda"
  role = var.sfn_role_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "InvokeLambda"
      Effect = "Allow"
      Action = ["lambda:InvokeFunction"]
      Resource = [
        var.file_validator_lambda_arn,
        var.ai_processor_lambda_arn,
        var.report_adapter_lambda_arn,
        var.error_logger_lambda_arn,
      ]
    }]
  })
}

resource "aws_sfn_state_machine" "workflow" {
  name     = "${var.project_name}-workflow"
  role_arn = var.sfn_role_arn
  type     = "STANDARD"

  definition = jsonencode({
    StartAt = "FileValidator"
    States = {
      FileValidator = {
        Type     = "Task"
        Resource = var.file_validator_lambda_arn
        Next     = "AIProcessor"
        Retry = [{
          ErrorEquals     = ["States.ALL"]
          IntervalSeconds = 2
          MaxAttempts     = 3
          BackoffRate     = 2
        }]
        Catch = [{
          ErrorEquals = ["States.ALL"]
          ResultPath  = "$.error"
          Next        = "ErrorLogger"
        }]
      }
      AIProcessor = {
        Type     = "Task"
        Resource = var.ai_processor_lambda_arn
        Next     = "ReportAdapter"
        Retry = [{
          ErrorEquals     = ["States.ALL"]
          IntervalSeconds = 2
          MaxAttempts     = 3
          BackoffRate     = 2
        }]
        Catch = [{
          ErrorEquals = ["States.ALL"]
          ResultPath  = "$.error"
          Next        = "ErrorLogger"
        }]
      }
      ReportAdapter = {
        Type     = "Task"
        Resource = var.report_adapter_lambda_arn
        Next     = "WorkflowSucceeded"
        Retry = [{
          ErrorEquals     = ["States.ALL"]
          IntervalSeconds = 2
          MaxAttempts     = 3
          BackoffRate     = 2
        }]
        Catch = [{
          ErrorEquals = ["States.ALL"]
          ResultPath  = "$.error"
          Next        = "ErrorLogger"
        }]
      }
      WorkflowSucceeded = {
        Type = "Succeed"
      }
      ErrorLogger = {
        Type     = "Task"
        Resource = var.error_logger_lambda_arn
        Next     = "WorkflowFailed"
      }
      WorkflowFailed = {
        Type  = "Fail"
        Cause = "Workflow failed after error logging"
      }
    }
  })

  depends_on = [aws_iam_role_policy.sfn_invoke_lambda]
}
