output "ingestion_queue_url" {
  description = "URL da fila SQS de ingestao"
  value       = aws_sqs_queue.ingestion_queue.url
}

output "ingestion_queue_arn" {
  description = "ARN da fila SQS de ingestao"
  value       = aws_sqs_queue.ingestion_queue.arn
}

output "ingestion_queue_name" {
  description = "Nome da fila SQS de ingestao"
  value       = aws_sqs_queue.ingestion_queue.name
}

output "dlq_url" {
  description = "URL da fila DLQ"
  value       = aws_sqs_queue.dead_letter_queue.url
}

output "dlq_arn" {
  description = "ARN da fila DLQ"
  value       = aws_sqs_queue.dead_letter_queue.arn
}

output "dlq_name" {
  description = "Nome da fila DLQ"
  value       = aws_sqs_queue.dead_letter_queue.name
}

output "result_mail_queue_url" {
  description = "URL da fila de envio de resultado"
  value       = aws_sqs_queue.result_mail_queue.url
}

output "result_mail_queue_arn" {
  description = "ARN da fila de envio de resultado"
  value       = aws_sqs_queue.result_mail_queue.arn
}

output "result_mail_queue_name" {
  description = "Nome da fila de envio de resultado"
  value       = aws_sqs_queue.result_mail_queue.name
}
