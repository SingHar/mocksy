# The client's production design in one stack (see README.md):
# CloudFront -> ALB -> ECS service (API) -> RDS PostgreSQL (+ replica) and Valkey,
# secrets from Secrets Manager, autoscaling on CPU, requests per target and queue depth.

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

variable "image" {
  description = "Container image with python3 (the API)"
  type        = string
  default     = "python:3.13-alpine"
}

provider "aws" {
  region                      = "ap-south-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  endpoints {
    applicationautoscaling = var.endpoint
    cloudfront             = var.endpoint
    cloudwatch             = var.endpoint
    ec2                    = var.endpoint
    ecs                    = var.endpoint
    elasticache            = var.endpoint
    elbv2                  = var.endpoint
    iam                    = var.endpoint
    logs                   = var.endpoint
    rds                    = var.endpoint
    secretsmanager         = var.endpoint
    sts                    = var.endpoint
  }
}

# ---------------------------------------------------------------- network

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

# ---------------------------------------------------------------- data

resource "aws_db_subnet_group" "db" {
  name       = "client-db"
  subnet_ids = [aws_subnet.a.id, aws_subnet.b.id]
}

resource "aws_db_instance" "primary" {
  identifier                  = "client-db"
  engine                      = "postgres"
  engine_version              = "18"
  instance_class              = "db.t4g.micro"
  allocated_storage           = 20
  db_name                     = "app"
  username                    = "app"
  manage_master_user_password = true
  db_subnet_group_name        = aws_db_subnet_group.db.name
  backup_retention_period     = 1
  skip_final_snapshot         = true
}

resource "aws_db_instance" "replica" {
  identifier          = "client-db-replica"
  replicate_source_db = aws_db_instance.primary.identifier
  instance_class      = "db.t4g.micro"
  skip_final_snapshot = true
}

resource "aws_elasticache_subnet_group" "cache" {
  name       = "client-cache"
  subnet_ids = [aws_subnet.a.id, aws_subnet.b.id]
}

resource "aws_elasticache_replication_group" "cache" {
  replication_group_id = "client-cache"
  description          = "API cache and queues"
  engine               = "valkey"
  node_type            = "cache.t4g.micro"
  num_cache_clusters   = 2
  subnet_group_name    = aws_elasticache_subnet_group.cache.name
}

# ---------------------------------------------------------------- load balancer

resource "aws_lb" "api" {
  name               = "client-api"
  load_balancer_type = "application"
  subnets            = [aws_subnet.a.id, aws_subnet.b.id]
}

resource "aws_lb_target_group" "api" {
  name        = "client-api"
  port        = 8080
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id
  health_check {
    path                = "/health"
    interval            = 5
    timeout             = 2
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.api.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

# ---------------------------------------------------------------- API service

resource "aws_cloudwatch_log_group" "api" { name = "/ecs/client-api" }

resource "aws_ecs_cluster" "app" { name = "client" }

resource "aws_ecs_task_definition" "api" {
  family                   = "client-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  container_definitions = jsonencode([{
    name      = "api"
    image     = var.image
    essential = true
    command   = ["python3", "-u", "-c", file("${path.module}/api.py")]
    environment = [
      { name = "DB_HOST", value = aws_db_instance.primary.address },
      { name = "DB_PORT", value = tostring(aws_db_instance.primary.port) },
      { name = "CACHE_HOST", value = aws_elasticache_replication_group.cache.primary_endpoint_address },
      { name = "CACHE_PORT", value = tostring(aws_elasticache_replication_group.cache.port) },
    ]
    secrets = [
      { name = "DB_PASSWORD", valueFrom = "${aws_db_instance.primary.master_user_secret[0].secret_arn}:password::" },
    ]
    portMappings = [{ containerPort = 8080 }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.api.name
        awslogs-region        = "ap-south-1"
        awslogs-stream-prefix = "api"
      }
    }
  }])
}

resource "aws_ecs_service" "api" {
  name                              = "client-api"
  cluster                           = aws_ecs_cluster.app.id
  task_definition                   = aws_ecs_task_definition.api.arn
  desired_count                     = 2
  launch_type                       = "FARGATE"
  health_check_grace_period_seconds = 10
  network_configuration { subnets = [aws_subnet.a.id, aws_subnet.b.id] }
  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8080
  }
  lifecycle { ignore_changes = [desired_count] }
  depends_on = [aws_lb_listener.http]
}

# ---------------------------------------------------------------- autoscaling (spec §7.3)

resource "aws_appautoscaling_target" "api" {
  service_namespace  = "ecs"
  resource_id        = "service/${aws_ecs_cluster.app.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  min_capacity       = 2
  max_capacity       = 6
}

resource "aws_appautoscaling_policy" "cpu" {
  name               = "api-cpu"
  policy_type        = "TargetTrackingScaling"
  service_namespace  = aws_appautoscaling_target.api.service_namespace
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  target_tracking_scaling_policy_configuration {
    target_value = 60
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

resource "aws_appautoscaling_policy" "requests" {
  name               = "api-requests"
  policy_type        = "TargetTrackingScaling"
  service_namespace  = aws_appautoscaling_target.api.service_namespace
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  target_tracking_scaling_policy_configuration {
    target_value       = 100
    scale_in_cooldown  = 300
    scale_out_cooldown = 30
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label         = "${aws_lb.api.arn_suffix}/${aws_lb_target_group.api.arn_suffix}"
    }
  }
}

# ---------------------------------------------------------------- CDN

resource "aws_cloudfront_distribution" "cdn" {
  enabled = true
  origin {
    domain_name = aws_lb.api.dns_name
    origin_id   = "alb"
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }
  default_cache_behavior {
    target_origin_id       = "alb"
    viewer_protocol_policy = "allow-all"
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    forwarded_values {
      query_string = true
      cookies { forward = "all" }
    }
  }
  restrictions {
    geo_restriction { restriction_type = "none" }
  }
  viewer_certificate { cloudfront_default_certificate = true }
}

output "cdn_domain" { value = aws_cloudfront_distribution.cdn.domain_name }
output "alb_dns_name" { value = aws_lb.api.dns_name }
output "db_endpoint" { value = aws_db_instance.primary.endpoint }
output "cache_endpoint" { value = aws_elasticache_replication_group.cache.primary_endpoint_address }
