// Bucket de entrada para arquivos de diagramas enviados ao sistema.
resource "aws_s3_bucket" "diagram_upload" {
  bucket = lower("${var.environment}-${var.project_name}-diagram-upload")
  tags = merge(var.tags, {
    Purpose = "Upload de diagramas"
    Module  = "analyzer"
  })
}

// Bucket para armazenar o resultado da analise dos diagramas.
resource "aws_s3_bucket" "analysis_result" {
  bucket = lower("${var.environment}-${var.project_name}-analysis-result")
  tags = merge(var.tags, {
    Purpose = "Resultado da analise dos diagramas"
    Module  = "analyzer"
  })
}

// Bucket de congelamento (longa retencao) para copias em armazenamento mais barato.
resource "aws_s3_bucket" "freeze" {
  bucket = lower("${var.environment}-${var.project_name}-freeze")
  tags = merge(var.tags, {
    Purpose = "Arquivos congelados"
    Module  = "analyzer"
  })
}

// Habilita versionamento no bucket de upload para suportar replicacao e trilha de alteracoes.
resource "aws_s3_bucket_versioning" "diagram_upload" {
  bucket = aws_s3_bucket.diagram_upload.id
  versioning_configuration {
    status = "Enabled"
  }
}

// Habilita versionamento no bucket de resultados de analise.
resource "aws_s3_bucket_versioning" "analysis_result" {
  bucket = aws_s3_bucket.analysis_result.id
  versioning_configuration {
    status = "Enabled"
  }
}

// Habilita versionamento no bucket freeze para manter historico dos objetos replicados.
resource "aws_s3_bucket_versioning" "freeze" {
  bucket = aws_s3_bucket.freeze.id
  versioning_configuration {
    status = "Enabled"
  }
}

// Ativa criptografia server-side padrao (SSE-S3/AES256) no bucket de upload.
resource "aws_s3_bucket_server_side_encryption_configuration" "diagram_upload" {
  bucket = aws_s3_bucket.diagram_upload.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

// Ativa criptografia server-side padrao no bucket de resultado da analise.
resource "aws_s3_bucket_server_side_encryption_configuration" "analysis_result" {
  bucket = aws_s3_bucket.analysis_result.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

// Ativa criptografia server-side padrao no bucket freeze.
resource "aws_s3_bucket_server_side_encryption_configuration" "freeze" {
  bucket = aws_s3_bucket.freeze.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

// Bloqueia qualquer forma de acesso publico no bucket de upload.
resource "aws_s3_bucket_public_access_block" "diagram_upload" {
  bucket = aws_s3_bucket.diagram_upload.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

// Bloqueia acesso publico no bucket de resultado da analise.
resource "aws_s3_bucket_public_access_block" "analysis_result" {
  bucket = aws_s3_bucket.analysis_result.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

// Bloqueia acesso publico no bucket freeze.
resource "aws_s3_bucket_public_access_block" "freeze" {
  bucket = aws_s3_bucket.freeze.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

// Role assumida pelo servico S3 para executar replicacao entre buckets.
resource "aws_iam_role" "s3_replication" {
  name = "${var.environment}-${var.project_name}-s3-replication"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

// Politica de permissoes da replicacao: leitura nas origens e escrita no destino freeze.
resource "aws_iam_policy" "s3_replication" {
  name = "${var.environment}-${var.project_name}-s3-replication"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.diagram_upload.arn,
          aws_s3_bucket.analysis_result.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging"
        ]
        Resource = [
          "${aws_s3_bucket.diagram_upload.arn}/*",
          "${aws_s3_bucket.analysis_result.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags"
        ]
        Resource = [
          "${aws_s3_bucket.freeze.arn}/*"
        ]
      }
    ]
  })
}

// Associa a politica de replicacao a role utilizada pelo S3.
resource "aws_iam_role_policy_attachment" "s3_replication" {
  role       = aws_iam_role.s3_replication.name
  policy_arn = aws_iam_policy.s3_replication.arn
}

// Regra de replicacao: copia objetos do bucket de upload para freeze em GLACIER_IR.
resource "aws_s3_bucket_replication_configuration" "diagram_upload_to_freeze" {
  role   = aws_iam_role.s3_replication.arn
  bucket = aws_s3_bucket.diagram_upload.id

  depends_on = [
    aws_s3_bucket_versioning.diagram_upload,
    aws_s3_bucket_versioning.freeze
  ]

  rule {
    id     = "diagram-upload-to-freeze"
    status = "Enabled"

    filter {
      prefix = ""
    }

    destination {
      bucket        = aws_s3_bucket.freeze.arn
      storage_class = "GLACIER_IR"
    }

    delete_marker_replication {
      status = "Enabled"
    }
  }
}

// Regra de replicacao: copia objetos do bucket de resultado para freeze em GLACIER_IR.
resource "aws_s3_bucket_replication_configuration" "analysis_result_to_freeze" {
  role   = aws_iam_role.s3_replication.arn
  bucket = aws_s3_bucket.analysis_result.id

  depends_on = [
    aws_s3_bucket_versioning.analysis_result,
    aws_s3_bucket_versioning.freeze
  ]

  rule {
    id     = "analysis-result-to-freeze"
    status = "Enabled"

    filter {
      prefix = ""
    }

    destination {
      bucket        = aws_s3_bucket.freeze.arn
      storage_class = "GLACIER_IR"
    }

    delete_marker_replication {
      status = "Enabled"
    }
  }
}

// Regra de ciclo de vida do bucket de upload: remove objetos correntes e nao correntes apos 30 dias.
resource "aws_s3_bucket_lifecycle_configuration" "diagram_upload" {
  bucket = aws_s3_bucket.diagram_upload.id

  rule {
    id     = "expire-after-30-days"
    status = "Enabled"

    filter {
      prefix = ""
    }

    expiration {
      days = 30
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

// Regra de ciclo de vida do bucket de resultado: remove objetos apos 30 dias.
resource "aws_s3_bucket_lifecycle_configuration" "analysis_result" {
  bucket = aws_s3_bucket.analysis_result.id

  rule {
    id     = "expire-after-30-days"
    status = "Enabled"

    filter {
      prefix = ""
    }

    expiration {
      days = 30
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}
