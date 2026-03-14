---
sidebar_position: 3
---

# EKS (Elastic Kubernetes Service)

Deploy FastAPI on Amazon EKS using **IAM Roles for Service Accounts (IRSA)** — each pod gets its own IAM role with no node-level credentials.

## When to choose EKS

- You need full Kubernetes control plane features
- Complex routing or multi-service microservices
- You want per-pod IAM isolation via IRSA

## Enable IRSA on your cluster

```bash
eksctl utils associate-iam-oidc-provider \
  --cluster my-cluster \
  --approve
```

## Create the IAM role

```bash
eksctl create iamserviceaccount \
  --name fastapi-sa \
  --namespace default \
  --cluster my-cluster \
  --attach-policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess \
  --approve \
  --override-existing-serviceaccounts
```

## Reference the service account in your pod

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-books
spec:
  template:
    spec:
      serviceAccountName: fastapi-sa   # <-- IRSA annotation lives here
      containers:
        - name: fastapi
          image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/fastapi-books:latest
          ports:
            - containerPort: 8000
```

`boto3` automatically picks up the IRSA token — your code is identical to the [Lambda secrets pattern](./aws-lambda.md#secrets-with-caching-parameters-utility).

## Next steps

- [AWS Lambda](./aws-lambda.md) — serverless, pay-per-invocation
- [ECS Fargate](./aws-ecs-fargate.md) — managed containers, no nodes to patch
- [Cloud IAM / Workload Identity](../auth/managed-identity.md) — how the credential chain works across clouds
