output "ingestion_queue_url" {
  description = "URL of the ingestion queue"
  value       = aws_sqs_queue.ingestion_queue.id
}

output "ingestion_queue_name" {
  description = "Name of the ingestion queue"
  value       = aws_sqs_queue.ingestion_queue.name
}

output "ingestion_queue_arn" {
  description = "ARN of the ingestion queue"
  value       = aws_sqs_queue.ingestion_queue.arn
}

output "ingestion_dlq_url" {
  description = "URL of the ingestion dead letter queue"
  value       = aws_sqs_queue.ingestion_dlq.id
}

output "ingestion_dlq_arn" {
  description = "ARN of the ingestion dead letter queue"
  value       = aws_sqs_queue.ingestion_dlq.arn
}

output "pdf_mail_queue_url" {
  description = "URL of the PDF/Mail queue"
  value       = aws_sqs_queue.pdf_mail_queue.id
}

output "pdf_mail_queue_arn" {
  description = "ARN of the PDF/Mail queue"
  value       = aws_sqs_queue.pdf_mail_queue.arn
}
