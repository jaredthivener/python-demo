---
sidebar_position: 2
---

# ECS Fargate

Deploy FastAPI on AWS Fargate — managed containers without EC2 instances to patch. Each task gets its own IAM role via ECS Task IAM Roles.

## When to choose ECS Fargate

- Long-running containers — no cold starts
- Managed containers, no nodes to patch
- Full VPC networking support
- ~$30+/month for an always-on service

## Task definition with task role

```json
{
  "family": "fastapi-books",
  "taskRoleArn": "arn:aws:iam::123456789012:role/fastapi-task-role",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "fastapi",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/fastapi-books:latest",
      "portMappings": [{ "containerPort": 8000 }],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/fastapi-books",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## Create the task role

```bash
aws iam create-role \
  --role-name fastapi-task-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "Service": "ecs-tasks.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }]
  }'

# Grant DynamoDB access (example)
aws iam put-role-policy \
  --role-name fastapi-task-role \
  --policy-name allow-dynamodb \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:Query", "dynamodb:Scan"],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/books"
    }]
  }'
```

## Deploy to Fargate

```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://task-def.json

# Create ECS cluster
aws ecs create-cluster --cluster-name fastapi-cluster

# Create service
aws ecs create-service \
  --cluster fastapi-cluster \
  --service-name fastapi-books \
  --task-definition fastapi-books:1 \
  --launch-type FARGATE \
  --desired-count 2 \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-abc123],securityGroups=[sg-xyz456],assignPublicIp=ENABLED}"
```

## Next steps

- [AWS Lambda](./aws-lambda.md) — serverless, pay-per-invocation
- [EKS](./aws-eks.md) — Kubernetes with IRSA
- [Cloud IAM / Workload Identity](../auth/managed-identity.md) — how the credential chain works across clouds
