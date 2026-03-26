variable "project_name" {
  description = "Project name used in S3 bucket names"
  type        = string
}

variable "environment" {
  description = "The environment for the deployment (e.g., dev, hom, prod)"
  type        = string
}

variable "tags" {
  description = "Tags for the S3 buckets"
  type        = map(string)
  default     = {}
}
