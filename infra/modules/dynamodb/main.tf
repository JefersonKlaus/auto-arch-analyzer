// DynamoDB single table para o projeto.
resource "aws_dynamodb_table" "project_table" {
  name         = "${var.project_name}-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  attribute {
    name = "GSI1PK"
    type = "S"
  }

  attribute {
    name = "GSI1SK"
    type = "S"
  }

  global_secondary_index {
    name            = "GSI1"
    hash_key        = "GSI1PK"
    range_key       = "GSI1SK"
    projection_type = "ALL"
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-table"
    Type = "single-table"
  })
}

// Itens iniciais da single table para configuracoes de debito direto.
resource "aws_dynamodb_table_item" "direct_debit_configs" {
  count      = length(var.direct_debit_configs)
  table_name = aws_dynamodb_table.project_table.name
  hash_key   = aws_dynamodb_table.project_table.hash_key
  range_key  = aws_dynamodb_table.project_table.range_key



  item = jsonencode(merge(
    {
      "PK"   = { "S" = "CONFIG#DIRECT_DEBIT" }
      "SK"   = { "S" = var.direct_debit_configs[count.index].id }
      "id"   = { "S" = var.direct_debit_configs[count.index].id }
      "bank" = { "S" = var.direct_debit_configs[count.index].bank }
      "name" = { "S" = var.direct_debit_configs[count.index].name }
    },
    # Adiciona todas as configurações específicas do banco dinamicamente
    { for key, value in var.direct_debit_configs[count.index].config : key => { "S" = tostring(value) } }
  ))
}
