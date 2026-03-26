variable "project_name" {
  description = "Project name used as a prefix for DynamoDB tables"
  type        = string
}

variable "tags" {
  description = "Tags to apply to DynamoDB tables"
  type        = map(string)
  default     = {}
}

variable "direct_debit_configs" {
  description = "List of direct debit bank configurations with flexible parameters (optional - only for admin table)"
  type = list(object({
    id     = string
    bank   = string
    name   = string
    config = map(any)
  }))
  default = []
}
