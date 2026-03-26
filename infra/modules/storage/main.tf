locals {
  name_prefix = "${lower(var.environment)}-${lower(var.project_name)}"
}

resource "aws_s3_bucket" "diagrams" {
  bucket = "${local.name_prefix}-diagrams"
}

resource "aws_s3_bucket" "reports_pdf" {
  bucket = "${local.name_prefix}-diagrams-result"
}

resource "aws_s3_bucket_public_access_block" "diagrams" {
  bucket                  = aws_s3_bucket.diagrams.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "reports_pdf" {
  bucket                  = aws_s3_bucket.reports_pdf.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "diagrams" {
  bucket = aws_s3_bucket.diagrams.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "reports_pdf" {
  bucket = aws_s3_bucket.reports_pdf.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "diagrams" {
  bucket = aws_s3_bucket.diagrams.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "reports_pdf" {
  bucket = aws_s3_bucket.reports_pdf.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_dynamodb_table" "reports" {
  name         = "${var.project_name}-findings"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "execution_id"

  attribute {
    name = "execution_id"
    type = "S"
  }

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }
}
