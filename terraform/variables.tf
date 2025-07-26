variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "ecr_repo_name" {
  type    = string
  default = "askpdf-lambda"
}

variable "lambda_function_name" {
  type    = string
  default = "askpdf-api"
}

# Secrets (no defaults—these must be provided)
variable "pinecone_api_key" {
  type = string
}

variable "pinecone_env" {
  type = string
}

variable "pinecone_index_name" {
  type = string
}

variable "openai_api_key" {
  type = string
}

variable "huggingfacehub_api_token" {
  type = string
}

variable "upload_bucket_name" {
  type    = string
}

