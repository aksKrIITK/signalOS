# SignalOS Production AWS Infrastructure Terraform Definition

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

variable "aws_region" {
  default = "us-east-1"
}

variable "environment" {
  default = "production"
}

# 1. VPC & Networking
resource "aws_vpc" "signalos_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = { Name = "signalos-${var.environment}-vpc" }
}

# 2. RDS PostgreSQL with pgvector
resource "aws_db_instance" "postgres" {
  identifier          = "signalos-${var.environment}-db"
  allocated_storage   = 100
  engine              = "postgres"
  engine_version      = "16.2"
  instance_class      = "db.r6g.xlarge"
  db_name             = "signalos"
  username            = "postgresadmin"
  password            = "secure_vault_managed_pwd_2026"
  skip_final_snapshot = true
}

# 3. ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "signalos-${var.environment}-redis"
  engine               = "redis"
  node_type            = "cache.r6g.large"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
}

# 4. SQS Queue for Asynchronous Campaign Batching
resource "aws_sqs_queue" "campaign_queue" {
  name                      = "signalos-campaign-queue-${var.environment}"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10
}

resource "aws_sqs_queue" "campaign_dlq" {
  name = "signalos-campaign-dlq-${var.environment}"
}

# 5. ECS Cluster & Fargate Services
resource "aws_ecs_cluster" "signalos_cluster" {
  name = "signalos-${var.environment}-cluster"
}

# 6. S3 Bucket for Knowledge Base & Raw HTML storage
resource "aws_s3_bucket" "knowledge_bucket" {
  bucket = "signalos-${var.environment}-knowledge-artifacts"
}
