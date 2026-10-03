variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "prod"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.environment))
    error_message = "environment must contain only lowercase letters, digits, and hyphens."
  }
}

variable "aws_region" {
  description = "AWS region for enterprise deployment."
  type        = string
  default     = "us-east-1"
}

variable "eks_version" {
  description = "EKS control-plane version."
  type        = string
  default     = "1.30"
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for EKS cluster and nodes."
  type        = list(string)
}

variable "eks_cluster_role_arn" {
  description = "IAM role ARN for EKS control plane."
  type        = string
}

variable "eks_node_role_arn" {
  description = "IAM role ARN for EKS node group."
  type        = string
}

variable "node_desired" {
  description = "Desired node count."
  type        = number
  default     = 6
}

variable "node_min" {
  description = "Minimum node count."
  type        = number
  default     = 3
}

variable "node_max" {
  description = "Maximum node count."
  type        = number
  default     = 30
}

variable "node_instance_types" {
  description = "Instance types for node group."
  type        = list(string)
  default     = ["m6i.large"]
}
