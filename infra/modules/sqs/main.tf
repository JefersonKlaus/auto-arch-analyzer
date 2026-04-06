# Fila de dead letter para mensagens que excederem o limite de tentativas.
resource "aws_sqs_queue" "dead_letter_queue" {
  name                      = "${var.project}-dead-letter-queue-${var.environment}"
  message_retention_seconds = var.message_retention_seconds

  tags = var.tags
}

# Fila de ingestao que recebe os inputs vindos do API Gateway.
resource "aws_sqs_queue" "ingestion_queue" {
  name                       = "${var.project}-ingestion-queue-${var.environment}"
  delay_seconds              = 0
  max_message_size           = 262144
  message_retention_seconds  = var.message_retention_seconds
  receive_wait_time_seconds  = 20 # Long polling
  visibility_timeout_seconds = var.ingestion_visibility_timeout_seconds

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead_letter_queue.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = var.tags
}

# Fila de resultados para envio assincrono de PDF/email.
resource "aws_sqs_queue" "result_mail_queue" {
  name                       = "${var.project}-result-mail-queue-${var.environment}"
  delay_seconds              = 0
  max_message_size           = 262144
  message_retention_seconds  = var.message_retention_seconds
  receive_wait_time_seconds  = 20
  visibility_timeout_seconds = var.result_mail_visibility_timeout_seconds

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead_letter_queue.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = var.tags
}

# CloudWatch Alarms para monitoramento
# Alarme para volume alto de mensagens pendentes na fila de ingestao.
resource "aws_cloudwatch_metric_alarm" "queue_messages_alarm" {
  alarm_name          = "${var.project}-ingestion-queue-messages-high-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ApproximateNumberOfVisibleMessages"
  namespace           = "AWS/SQS"
  period              = "300"
  statistic           = "Average"
  threshold           = "100"
  alarm_description   = "This metric monitors queue message count"
  alarm_actions       = var.alarm_actions

  dimensions = {
    QueueName = aws_sqs_queue.ingestion_queue.name
  }

  tags = var.tags
}

# Alarme para volume alto de mensagens pendentes na fila de resultados.
resource "aws_cloudwatch_metric_alarm" "result_mail_queue_messages_alarm" {
  alarm_name          = "${var.project}-result-mail-queue-messages-high-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ApproximateNumberOfVisibleMessages"
  namespace           = "AWS/SQS"
  period              = "300"
  statistic           = "Average"
  threshold           = "100"
  alarm_description   = "This metric monitors result/mail queue message count"
  alarm_actions       = var.alarm_actions

  dimensions = {
    QueueName = aws_sqs_queue.result_mail_queue.name
  }

  tags = var.tags
}

# Alarme para qualquer mensagem enviada para a dead letter queue.
resource "aws_cloudwatch_metric_alarm" "dlq_messages_alarm" {
  alarm_name          = "${var.project}-dead-letter-queue-messages-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfVisibleMessages"
  namespace           = "AWS/SQS"
  period              = "60"
  statistic           = "Average"
  threshold           = "0"
  alarm_description   = "This metric monitors DLQ message count"
  alarm_actions       = var.alarm_actions

  dimensions = {
    QueueName = aws_sqs_queue.dead_letter_queue.name
  }

  tags = var.tags
}
