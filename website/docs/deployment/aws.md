---
sidebar_position: 2
---

# AWS Deployment

Deploy FastAPI to AWS with zero long-lived credentials using Lambda execution roles, IAM Roles for Service Accounts (IRSA) on EKS, or instance profiles.

## Choose your target

|                       | Lambda + Mangum                  | EKS + IRSA                           | Elastic Beanstalk      |
| --------------------- | -------------------------------- | ------------------------------------ | ---------------------- |
| **Cost at idle**      | $0 (pay per invocation)          | ~$100+/month+                        | ~$20+/month (t3.micro) |
| **Cold start?**       | Yes (mitigable with provisioned) | No                                   | No                     |
| **IAM auth**          | Lambda execution role            | IAM Roles for Service Accounts       | Instance profile       |
| **Container support** | Yes (container image)            | Native                               | Yes (Docker platform)  |
| **Custom networking** | VPC Lambda                       | Full VPC                             | VPC                    |
| **Best for**          | Event-driven / spiky traffic     | Kubernetes / multi-service platforms | Monolithic web APIs    |

---

## Option A — AWS Lambda with Mangum

[Mangum](https://github.com/jordaneremieff/mangum) wraps any ASGI app (FastAPI, Starlette) to run on Lambda.

### Install

```bash
uv add mangum
```

### Wrap the app

```python
# lambda_handler.py
from mangum import Mangum
from demo.main import app   # your FastAPI app

handler = Mangum(app, lifespan="off")
```

### IAM — Lambda execution role

Create a Lambda execution role in IAM and attach the permissions your function needs. The role is automatically provided to your function — **no access keys required**.

```bash
# Create the execution role
aws iam create-role \
  --role-name fastapi-lambda-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach basic execution policy (CloudWatch Logs)
aws iam attach-role-policy \
  --role-name fastapi-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Grant access to a Secrets Manager secret (example)
aws iam put-role-policy \
  --role-name fastapi-lambda-role \
  --policy-name allow-secret \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret-*"
    }]
  }'
```

### Deploy with container image

```bash
# Build and push to ECR
aws ecr create-repository --repository-name fastapi-books
aws ecr get-login-password | docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com

docker build -t fastapi-books .
docker tag fastapi-books:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/fastapi-books:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/fastapi-books:latest

# Create the Lambda function
aws lambda create-function \
  --function-name fastapi-books \
  --package-type Image \
  --code ImageUri=123456789012.dkr.ecr.us-east-1.amazonaws.com/fastapi-books:latest \
  --role arn:aws:iam::123456789012:role/fastapi-lambda-role
```

### Access AWS services from FastAPI without credentials

The Lambda execution role is picked up automatically by the AWS SDK (`boto3`):

```python
import boto3
import json
from functools import lru_cache

@lru_cache
def get_secret(secret_name: str) -> dict:
    """Retrieve a secret from Secrets Manager using the Lambda IAM role."""
    client = boto3.client("secretsmanager")          # no credentials needed
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])
```

---

## Option B — IRSA on EKS

If you're running on Kubernetes (EKS), use **IAM Roles for Service Accounts (IRSA)** to give each pod its own IAM role — no node-level credentials.

### Enable IRSA on your cluster

```bash
eksctl utils associate-iam-oidc-provider \
  --cluster my-cluster \
  --approve
```

### Create the IAM role

```bash
eksctl create iamserviceaccount \
  --name fastapi-sa \
  --namespace default \
  --cluster my-cluster \
  --attach-policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess \
  --approve \
  --override-existing-serviceaccounts
```

### Reference the service account in your pod

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-books
spec:
  template:
    spec:
      serviceAccountName: fastapi-sa # <-- IRSA annotation lives here
      containers:
        - name: fastapi
          image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/fastapi-books:latest
          ports:
            - containerPort: 8000
```

`boto3` automatically picks up the IRSA token — your code is identical to the Lambda example above.

---

## Option C — ECS Fargate with Task Role

Fargate runs containers without managing EC2 instances. Each task gets an IAM role via ECS Task IAM Roles.

### Task definition with task role

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

### Create the task role

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

### Deploy to Fargate

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

---

## Reading AWS secrets in FastAPI

```python
import os
import boto3
import json
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    client = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION", "us-east-1"))
    secret = client.get_secret_value(SecretId=os.environ["SECRET_ARN"])
    data = json.loads(secret["SecretString"])
    app.state.jwt_secret = data["jwt_secret"]
    yield

app = FastAPI(lifespan=lifespan)
```

No hardcoded credentials — the IAM role (Lambda execution role, ECS task role, or IRSA) is resolved at runtime by the SDK.

---

## Next steps

- [Cloud IAM / Workload Identity](../auth/managed-identity.md) — how the credential chain works across clouds
- [GCP Deployment](./gcp.md) — Cloud Run + Workload Identity
- [Azure Functions](./azure-functions.md) — Azure equivalent
