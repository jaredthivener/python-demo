---
sidebar_position: 1
---

# AWS Lambda

Deploy FastAPI as a serverless Lambda function using [Mangum](https://github.com/jordaneremieff/mangum) and [AWS Lambda Powertools](https://docs.powertools.aws.dev/lambda/python/latest/) — the AWS-built toolkit for production observability (Logger, Tracer, Metrics, and Parameters).

## When to choose Lambda

- Spiky or infrequent traffic — pay $0 at idle (pay per invocation)
- Event-driven triggers: HTTP via API Gateway v2, SQS, SNS, EventBridge
- Zero infrastructure management
- Cold start latency is acceptable (mitigable with provisioned concurrency)

## Install

```bash
uv add mangum "aws-lambda-powertools[all]"
```

`aws-lambda-powertools[all]` includes Logger, Tracer, Metrics, and the Parameters utility in one install.

:::info What is Mangum?
AWS Lambda receives HTTP requests as a raw JSON dictionary (`event`, `context`) — it has no built-in support for ASGI frameworks like FastAPI. **[Mangum](https://github.com/jordaneremieff/mangum)** is a lightweight adapter that translates between the two:

```
API Gateway → Lambda event dict → Mangum → ASGI scope → FastAPI → response → Mangum → Lambda response dict → API Gateway
```

You wrap your FastAPI app once at module level (`Mangum(app, lifespan="off")`), and your Lambda handler just calls it like a normal function. `lifespan="off"` disables FastAPI's startup/shutdown events, which don't apply to Lambda's ephemeral execution model.
:::

## Lambda handler

```python
# lambda_handler.py
from mangum import Mangum
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit  # noqa: F401 — used by routes
from demo.main import app

logger = Logger(service="fastapi-books")
tracer = Tracer(service="fastapi-books")
metrics = Metrics(namespace="FastAPIBooks", service="fastapi-books")

# Wrap the FastAPI ASGI app once at module level (warm starts reuse this)
_mangum_handler = Mangum(app, lifespan="off")


@logger.inject_lambda_context(correlation_id_path="requestContext.requestId", log_event=False)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict, context: object) -> dict:
    return _mangum_handler(event, context)
```

The three decorators give you out-of-the-box:

| Decorator | What it adds |
|---|---|
| `@logger.inject_lambda_context` | Request ID, function name, cold start flag on every log line |
| `@tracer.capture_lambda_handler` | AWS X-Ray subsegment for the full invocation |
| `@metrics.log_metrics` | Flushes CloudWatch EMF metrics; records `ColdStart` count automatically |

## Required environment variables

Set these on the Lambda function (not in code):

```bash
POWERTOOLS_SERVICE_NAME=fastapi-books
POWERTOOLS_METRICS_NAMESPACE=FastAPIBooks
LOG_LEVEL=INFO
POWERTOOLS_TRACER_CAPTURE_RESPONSE=false   # prevents full response bodies in traces
SECRET_ARN=arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret
```

## Secrets with caching (Parameters utility)

The **Parameters utility** caches values in memory with a configurable TTL — no Secrets Manager call on every warm invocation:

```python
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator
from aws_lambda_powertools.utilities.parameters import get_secret
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Fetches once on cold start; refreshes automatically after max_age seconds
    secret: dict = get_secret(  # type: ignore[assignment]
        os.environ["SECRET_ARN"], transform="json", max_age=300
    )
    app.state.jwt_secret = secret["jwt_secret"]
    app.state.db_password = secret["db_password"]
    yield


app = FastAPI(lifespan=lifespan)
```

## Structured logging inside routes

```python
from aws_lambda_powertools import Logger

logger = Logger(service="fastapi-books")


@app.get("/api/v1/books/{book_id}")
async def get_book(book_id: str):
    logger.info("Fetching book", extra={"book_id": book_id})
    ...
```

Every line is emitted as structured JSON and indexed in CloudWatch Logs Insights automatically.

## Custom metrics

```python
from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit

metrics = Metrics(namespace="FastAPIBooks")


@app.post("/api/v1/books")
async def create_book(book: BookCreate):
    metrics.add_metric(name="BooksCreated", unit=MetricUnit.Count, value=1)
    ...
```

Metrics are flushed to CloudWatch automatically at the end of each invocation by the `@metrics.log_metrics` decorator.

## IAM — Lambda execution role

Create a least-privilege execution role:

```bash
# Create execution role
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

# CloudWatch Logs
aws iam attach-role-policy \
  --role-name fastapi-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# X-Ray tracing (required for @tracer.capture_lambda_handler)
aws iam attach-role-policy \
  --role-name fastapi-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess

# Secrets Manager — scope to the specific secret ARN
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

## Deploy with container image

```bash
# Build and push to ECR
aws ecr create-repository --repository-name fastapi-books
aws ecr get-login-password | docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com

docker build -t fastapi-books .
docker tag fastapi-books:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/fastapi-books:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/fastapi-books:latest

# Create the Lambda function with Active X-Ray tracing
aws lambda create-function \
  --function-name fastapi-books \
  --package-type Image \
  --code ImageUri=123456789012.dkr.ecr.us-east-1.amazonaws.com/fastapi-books:latest \
  --role arn:aws:iam::123456789012:role/fastapi-lambda-role \
  --tracing-config Mode=Active \
  --environment Variables="{POWERTOOLS_SERVICE_NAME=fastapi-books,POWERTOOLS_METRICS_NAMESPACE=FastAPIBooks,LOG_LEVEL=INFO,POWERTOOLS_TRACER_CAPTURE_RESPONSE=false,SECRET_ARN=arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret}"
```

:::tip Provisioned Concurrency
For latency-sensitive APIs, enable provisioned concurrency to eliminate cold starts entirely:
```bash
aws lambda put-provisioned-concurrency-config \
  --function-name fastapi-books \
  --qualifier 1 \
  --provisioned-concurrent-executions 5
```
:::

## Next steps

- [ECS Fargate](./aws-ecs-fargate.md) — managed containers, no cold starts
- [EKS](./aws-eks.md) — Kubernetes with IRSA
- [Cloud IAM / Workload Identity](../auth/managed-identity.md) — how the credential chain works across clouds
