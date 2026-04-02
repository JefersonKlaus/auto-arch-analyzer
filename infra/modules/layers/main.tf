# Lambda Layers Module

# Common Layer
data "archive_file" "common_layer_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../src/layers/common"
  output_path = "${path.module}/zip/common_layer_payload.zip"
}

data "local_file" "common_layer_hash" {
  filename = data.archive_file.common_layer_zip.output_path
}

resource "aws_lambda_layer_version" "common_layer" {
  filename            = data.archive_file.common_layer_zip.output_path
  layer_name          = "${var.project_name}_${var.environment}_common_layer"
  compatible_runtimes = ["python3.10", "python3.11"]

  source_code_hash = data.local_file.common_layer_hash.content_base64
}

# # Dependencies Layer
# data "archive_file" "dependencies_layer_zip" {
#   type        = "zip"
#   source_dir  = "${path.root}/src/layers/dependencies"
#   output_path = "${path.module}/zip/dependencies_layer_payload.zip"
# }

# data "local_file" "dependencies_layer_hash" {
#   filename = data.archive_file.dependencies_layer_zip.output_path
# }

# resource "aws_lambda_layer_version" "dependencies_layer" {
#   filename            = data.archive_file.dependencies_layer_zip.output_path
#   layer_name          = "${var.project_name}_${var.environment}_dependencies_layer"
#   compatible_runtimes = ["python3.11"]

#   source_code_hash = data.local_file.dependencies_layer_hash.content_base64
# }
