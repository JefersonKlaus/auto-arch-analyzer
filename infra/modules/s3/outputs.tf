output "diagram_upload_bucket_name" {
  description = "Name of the bucket for diagram uploads"
  value       = aws_s3_bucket.diagram_upload.bucket
}

output "diagram_upload_bucket_arn" {
  description = "ARN of the bucket for diagram uploads"
  value       = aws_s3_bucket.diagram_upload.arn
}

output "analysis_result_bucket_name" {
  description = "Name of the bucket for analysis results"
  value       = aws_s3_bucket.analysis_result.bucket
}

output "analysis_result_bucket_arn" {
  description = "ARN of the bucket for analysis results"
  value       = aws_s3_bucket.analysis_result.arn
}

output "freeze_bucket_name" {
  description = "Name of the bucket for frozen files"
  value       = aws_s3_bucket.freeze.bucket
}

output "freeze_bucket_arn" {
  description = "ARN of the bucket for frozen files"
  value       = aws_s3_bucket.freeze.arn
}