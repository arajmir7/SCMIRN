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
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  tags                 = local.common_tags
}

resource "aws_s3_bucket" "briefings" {
  bucket = "${local.name_prefix}-executive-briefings"
  tags   = local.common_tags
}

resource "aws_s3_bucket_versioning" "briefings_versioning" {
  bucket = aws_s3_bucket.briefings.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_eks_cluster" "enterprise" {
  name     = "${local.name_prefix}-eks"
  role_arn = var.eks_cluster_role_arn
  version  = var.eks_version

  vpc_config {
    subnet_ids = var.private_subnet_ids
  }

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
