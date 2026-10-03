terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  name_prefix = "scmirn-${var.environment}"
  common_tags = {
    project     = "SCMIRN"
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "aws_ecr_repository" "backend" {
  name                 = "${local.name_prefix}-backend"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = false
  tags                 = local.common_tags

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }
}

resource "aws_kms_key" "eks_secrets" {
  description             = "Encrypt Kubernetes secrets for ${local.name_prefix}"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  tags                    = local.common_tags
}

resource "aws_kms_alias" "eks_secrets" {
  name          = "alias/${local.name_prefix}-eks-secrets"
  target_key_id = aws_kms_key.eks_secrets.key_id
}

resource "aws_kms_key" "briefings" {
  description             = "Encrypt ${local.name_prefix} briefing objects"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  tags                    = local.common_tags
}

resource "aws_kms_alias" "briefings" {
  name          = "alias/${local.name_prefix}-briefings"
  target_key_id = aws_kms_key.briefings.key_id
}

resource "aws_kms_key" "ecr" {
  description             = "Encrypt ${local.name_prefix} container images"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  tags                    = local.common_tags
}

resource "aws_s3_bucket" "briefings" {
  bucket = "${local.name_prefix}-executive-briefings"
  tags   = local.common_tags
}

resource "aws_s3_bucket" "briefings_access_logs" {
  bucket = "${local.name_prefix}-briefings-access-logs"
  tags   = local.common_tags
}

resource "aws_s3_bucket_versioning" "briefings_access_logs" {
  bucket = aws_s3_bucket.briefings_access_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "briefings_access_logs" {
  bucket                  = aws_s3_bucket.briefings_access_logs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "briefings_access_logs" {
  bucket = aws_s3_bucket.briefings_access_logs.id

  rule {
    apply_server_side_encryption_by_default {
      # S3 server access log destination buckets require SSE-S3 so delivered
      # log objects remain readable by the service log-delivery pipeline.
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "briefings_versioning" {
  bucket = aws_s3_bucket.briefings.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "briefings" {
  bucket                  = aws_s3_bucket.briefings.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "briefings" {
  bucket = aws_s3_bucket.briefings.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.briefings.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_policy" "briefings_require_tls" {
  bucket = aws_s3_bucket.briefings.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource = [
        aws_s3_bucket.briefings.arn,
        "${aws_s3_bucket.briefings.arn}/*"
      ]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket_policy" "briefings_access_logs" {
  bucket = aws_s3_bucket.briefings_access_logs.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "S3ServerAccessLogsPolicy"
      Effect    = "Allow"
      Principal = { Service = "logging.s3.amazonaws.com" }
      Action    = "s3:PutObject"
      Resource  = "${aws_s3_bucket.briefings_access_logs.arn}/s3-access/*"
      Condition = {
        ArnLike      = { "aws:SourceArn" = aws_s3_bucket.briefings.arn }
        StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
      }
    }]
  })
}

resource "aws_s3_bucket_logging" "briefings" {
  bucket        = aws_s3_bucket.briefings.id
  target_bucket = aws_s3_bucket.briefings_access_logs.id
  target_prefix = "s3-access/"

  depends_on = [aws_s3_bucket_policy.briefings_access_logs]
}

resource "aws_eks_cluster" "enterprise" {
  name     = "${local.name_prefix}-eks"
  role_arn = var.eks_cluster_role_arn
  version  = var.eks_version

  vpc_config {
    subnet_ids              = var.private_subnet_ids
    endpoint_private_access = true
    endpoint_public_access  = false
  }

  encryption_config {
    provider {
      key_arn = aws_kms_key.eks_secrets.arn
    }
    resources = ["secrets"]
  }

  enabled_cluster_log_types = [
    "api",
    "audit",
    "authenticator",
    "controllerManager",
    "scheduler"
  ]

  depends_on = [
    aws_kms_alias.eks_secrets
  ]

  tags = local.common_tags
}

resource "aws_eks_node_group" "enterprise_nodes" {
  cluster_name    = aws_eks_cluster.enterprise.name
  node_group_name = "${local.name_prefix}-nodes"
  node_role_arn   = var.eks_node_role_arn
  subnet_ids      = var.private_subnet_ids

  scaling_config {
    desired_size = var.node_desired
    min_size     = var.node_min
    max_size     = var.node_max
  }

  instance_types = var.node_instance_types
  tags           = local.common_tags
}
