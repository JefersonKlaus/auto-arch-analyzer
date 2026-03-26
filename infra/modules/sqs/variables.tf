variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "The environment for the deployment (e.g., dev, hom, prod)"
  type        = string
  default     = "dev"
}

variable "tags" {
  description = "Tags to be applied to resources"
  type        = map(string)
  default     = {}
}

variable "message_retention_seconds" {
  description = "Retention period for SQS messages"
  type        = number
  default     = 1209600
}

variable "ingestion_visibility_timeout_seconds" {
  description = "Visibility timeout for ingestion queue"
  type        = number
  default     = 300
}

variable "result_mail_visibility_timeout_seconds" {
  description = "Visibility timeout for result/mail queue"
  type        = number
  default     = 900
}

variable "max_receive_count" {
  description = "Max receives before moving a message to DLQ"
  type        = number
  default     = 3
}

variable "alarm_actions" {
  description = "List of ARNs for alarm actions (e.g., SNS topics)"
  type        = list(string)
  default     = []
}
