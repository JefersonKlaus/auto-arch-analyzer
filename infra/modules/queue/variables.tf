variable "project_name" {
  description = "Project name used as prefix for queue resources"
  type        = string
}

variable "ingestion_visibility_timeout_seconds" {
  description = "Visibility timeout for ingestion queue"
  type        = number
  default     = 300
}

variable "message_retention_seconds" {
  description = "Retention period for SQS messages"
  type        = number
  default     = 1209600
}

variable "ingestion_max_receive_count" {
  description = "Max receives before moving a message to DLQ"
  type        = number
  default     = 3
}
