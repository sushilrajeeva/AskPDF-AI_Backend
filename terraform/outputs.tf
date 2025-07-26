output "api_endpoint" {
  description = "Base URL for your service"
  value       = aws_apigatewayv2_api.http_api.api_endpoint
}

output "lambda_name" {
  value = aws_lambda_function.api.function_name
}

output "pdf_upload_bucket" {
  description = "S3 bucket storing uploaded PDFs"
  value       = aws_s3_bucket.pdf_uploads.bucket
}

output "chat_history_table" {
  description = "DynamoDB table for chat history"
  value       = aws_dynamodb_table.chat_history.name
}