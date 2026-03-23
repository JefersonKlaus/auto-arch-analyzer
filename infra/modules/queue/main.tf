resource "aws_sqs_queue" "ingestion_dlq" {
  name                      = "${var.project_name}-ingestion-dlq"
  message_retention_seconds = var.message_retention_seconds
}

resource "aws_sqs_queue" "ingestion_queue" {
  name                       = "${var.project_name}-ingestion-queue"
  visibility_timeout_seconds = var.ingestion_visibility_timeout_seconds
  message_retention_seconds  = var.message_retention_seconds

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ingestion_dlq.arn
    maxReceiveCount     = var.ingestion_max_receive_count
  })
}

resource "aws_sqs_queue" "pdf_mail_queue" {
  name                      = "${var.project_name}-pdf-mail-queue"
  message_retention_seconds = var.message_retention_seconds
}
