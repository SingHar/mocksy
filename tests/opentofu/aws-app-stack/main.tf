terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}

variable "endpoint" {
  description = "mocksy endpoint"
  type        = string
  default     = "http://localhost:4566"
}

provider "aws" {
  region                      = "ap-south-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  endpoints {
    ec2         = var.endpoint
    ecs         = var.endpoint
    rds         = var.endpoint
    elasticache = var.endpoint
    cloudfront  = var.endpoint
    iam         = var.endpoint
    sts         = var.endpoint
  }
}

resource "aws_vpc" "main" { cidr_block = "10.0.0.0/16" }

resource "aws_subnet" "a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "ap-south-1a"
}

resource "aws_subnet" "b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "ap-south-1b"
}

resource "aws_ecs_cluster" "app" { name = "app" }

resource "aws_ecs_task_definition" "api" {
  family                   = "api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  container_definitions = jsonencode([{
    name = "api", image = "nginx:stable", essential = true,
    portMappings = [{ containerPort = 80 }]
  }])
}

resource "aws_ecs_service" "api" {
  name            = "api"
  cluster         = aws_ecs_cluster.app.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  network_configuration { subnets = [aws_subnet.a.id, aws_subnet.b.id] }
}

resource "aws_db_subnet_group" "db" {
  name       = "db"
  subnet_ids = [aws_subnet.a.id, aws_subnet.b.id]
}

resource "aws_db_instance" "primary" {
  identifier              = "app-db"
  engine                  = "postgres"
  engine_version          = "18"
  instance_class          = "db.t4g.micro"
  allocated_storage       = 20
  username                = "app"
  password                = "change-me-123"
  db_subnet_group_name    = aws_db_subnet_group.db.name
  backup_retention_period = 1
  skip_final_snapshot     = true
}

resource "aws_db_instance" "replica" {
  identifier          = "app-db-replica"
  replicate_source_db = aws_db_instance.primary.identifier
  instance_class      = "db.t4g.micro"
  skip_final_snapshot = true
}

resource "aws_elasticache_subnet_group" "cache" {
  name       = "cache"
  subnet_ids = [aws_subnet.a.id, aws_subnet.b.id]
}

resource "aws_elasticache_replication_group" "cache" {
  replication_group_id = "app-cache"
  description          = "app cache"
  engine               = "valkey"
  node_type            = "cache.t4g.micro"
  num_cache_clusters   = 2
  subnet_group_name    = aws_elasticache_subnet_group.cache.name
}

resource "aws_cloudfront_distribution" "cdn" {
  enabled = true
  origin {
    domain_name = "api.example.com"
    origin_id   = "api"
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }
  default_cache_behavior {
    target_origin_id       = "api"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }
  }
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }
  restrictions {
    geo_restriction { restriction_type = "none" }
  }
  viewer_certificate { cloudfront_default_certificate = true }
}

output "db_endpoint" { value = aws_db_instance.primary.endpoint }
output "cache_endpoint" { value = aws_elasticache_replication_group.cache.primary_endpoint_address }
output "cdn_domain" { value = aws_cloudfront_distribution.cdn.domain_name }
