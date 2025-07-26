# Fetch existing ECR repo latest image
data "aws_ecr_image" "askpdf_image" {
  repository_name = var.ecr_repo_name
  image_tag       = "latest"
}

# IAM: Lambda assume role
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name               = "${var.lambda_function_name}-exec"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}


# Attach CloudWatch Logs policy
data "aws_iam_policy_document" "lambda_logs" {
  statement {
    actions   = ["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
}
resource "aws_iam_policy" "lambda_logs" {
  name   = "${var.lambda_function_name}-logs"
  policy = data.aws_iam_policy_document.lambda_logs.json
}
resource "aws_iam_role_policy_attachment" "logs_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_logs.arn
}

# S3 bucket to persist uploaded PDFs
resource "aws_s3_bucket" "pdf_uploads" {
  bucket = var.upload_bucket_name
  tags = {
    Project = "AskPDF-AI"
    Env     = "prod"
  }
}

# IAM policy allowing S3 Get/Put on our bucket
resource "aws_iam_policy" "s3_access" {
  name = "${var.lambda_function_name}-s3-access"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "AllowPDFUploadAccess"
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetObject"]
        Resource = "${aws_s3_bucket.pdf_uploads.arn}/*"
      }
    ]
  })
}

# Attach it to the Lambda execution role
resource "aws_iam_role_policy_attachment" "s3_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.s3_access.arn
}

# Lambda function from ECR image
resource "aws_lambda_function" "api" {
  function_name = var.lambda_function_name
  package_type  = "Image"
  image_uri     = data.aws_ecr_image.askpdf_image.image_uri
  role          = aws_iam_role.lambda_exec.arn

  # Tell Lambda to use the ARM64 (Graviton2) runtime
  architectures = ["arm64"]

  timeout       = 900
  memory_size   = 2048

  environment {
    variables = {
      PINECONE_API_KEY          = var.pinecone_api_key
      PINECONE_ENV              = var.pinecone_env
      PINECONE_INDEX_NAME       = var.pinecone_index_name
      OPENAI_API_KEY            = var.openai_api_key
      HUGGINGFACEHUB_API_TOKEN  = var.huggingfacehub_api_token
      PDF_UPLOAD_BUCKET         = aws_s3_bucket.pdf_uploads.bucket
      CHAT_HISTORY_TABLE        = aws_dynamodb_table.chat_history.name
    }
  }
}

# HTTP API Gateway
resource "aws_apigatewayv2_api" "http_api" {
  name          = "${var.lambda_function_name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["https://ask-pdf-ai.sushilbhandary.com"]
    allow_methods = ["OPTIONS", "GET", "POST"]
    allow_headers = ["*"]
    max_age       = 3600
  }
}

# Permission for API Gateway to invoke Lambda
resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowExecFromAPIGW"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

# Proxy integration & default route (catch-all)
resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}
resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}
resource "aws_apigatewayv2_stage" "prod" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_dynamodb_table" "chat_history" {
  name         = "${var.lambda_function_name}-history"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "chat_id"

  attribute {
    name = "chat_id"
    type = "S"
  }

  tags = {
    Project = "AskPDF-AI"
    Env     = "prod"
  }
}

resource "aws_iam_role_policy_attachment" "dynamo_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}
