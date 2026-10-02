output "eks_cluster_name" {
  description = "Enterprise EKS cluster name."
  value       = aws_eks_cluster.enterprise.name
}

output "backend_ecr_repository_url" {
  description = "ECR repository URL for backend image."
  value       = aws_ecr_repository.backend.repository_url
}

output "briefings_bucket_name" {
  description = "S3 bucket used for executive briefing artifacts."
  value       = aws_s3_bucket.briefings.bucket
}
