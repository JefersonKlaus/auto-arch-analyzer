variable "project_name" {
  description = "Project name used as prefix for API and queue resources"
  type        = string
}

variable "environment" {
  description = "Deployment environment used as API Gateway stage name"
  type        = string
}

variable "aws_region" {
  description = "AWS region where resources are deployed"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID used to build API Gateway -> Lambda integration URI"
  type        = string
}


