resource "aws_iam_role_policy" "sfn_invoke_lambda" {
  name = "${var.project_name}-sfn-invoke-lambda"
  role = var.sfn_role_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid      = "InvokeLambda"
      Effect   = "Allow"
      Action   = ["lambda:InvokeFunction"]
      Resource = var.lambda_function_arn
    }]
  })
}

resource "aws_sfn_state_machine" "workflow" {
  name     = "${var.project_name}-workflow"
  role_arn = var.sfn_role_arn
  type     = "STANDARD"

  definition = jsonencode({
    StartAt = "Processing"
    States = {
      Processing = {
        Type     = "Task"
        Resource = var.lambda_function_arn
        Next     = "Analyzed"
        Retry = [{
          ErrorEquals     = ["States.ALL"]
          IntervalSeconds = 2
          MaxAttempts     = 3
          BackoffRate     = 2
        }]
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "Error"
        }]
      }
      Analyzed = {
        Type = "Pass"
        End  = true
      }
      Error = {
        Type  = "Fail"
        Cause = "Critical failure during AI processing."
      }
    }
  })

  depends_on = [aws_iam_role_policy.sfn_invoke_lambda]
}
