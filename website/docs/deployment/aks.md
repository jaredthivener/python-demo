---
sidebar_position: 3
---

# AKS (Azure Kubernetes Service)

Deploy FastAPI on Kubernetes with Workload Identity for pod-level Managed Identity — the modern, secure approach.

## When to choose AKS

- Complex microservices where multiple containers need to interoperate
- High-throughput APIs that need horizontal pod autoscaling (HPA)
- Custom networking, service mesh (Istio/Linkerd), or sidecar requirements
- WebSockets, gRPC, or long-lived connections that don't fit the serverless model
- Your team already operates Kubernetes

:::info Use Workload Identity, not Pod Identity
Azure AD Pod Identity is deprecated. Use **Workload Identity** (OIDC federation) — it's more secure and supported long-term.
:::

## Architecture

```
Client → Azure Load Balancer → Ingress (NGINX/AGIC) → FastAPI pod
FastAPI pod → Azure Token Service (via OIDC) → Key Vault / SQL
```

## Enable OIDC and Workload Identity on your cluster

```bash
# Enable OIDC issuer and Workload Identity on an existing cluster
az aks update \
  --name my-aks-cluster \
  --resource-group my-rg \
  --enable-oidc-issuer \
  --enable-workload-identity

# Get the OIDC issuer URL (needed for federation)
OIDC_ISSUER=$(az aks show --name my-aks-cluster --resource-group my-rg \
  --query "oidcIssuerProfile.issuerUrl" -o tsv)
```

## Create a Managed Identity and federate it

```bash
# Create a user-assigned Managed Identity
az identity create \
  --name fastapi-books-identity \
  --resource-group my-rg

MI_CLIENT_ID=$(az identity show --name fastapi-books-identity \
  --resource-group my-rg --query clientId -o tsv)
MI_OBJECT_ID=$(az identity show --name fastapi-books-identity \
  --resource-group my-rg --query principalId -o tsv)

# Create a Kubernetes service account
kubectl create serviceaccount fastapi-sa --namespace default
kubectl annotate serviceaccount fastapi-sa \
  azure.workload.identity/client-id="$MI_CLIENT_ID" \
  --namespace default

# Federate the MI with the service account
az identity federated-credential create \
  --name fastapi-federated \
  --identity-name fastapi-books-identity \
  --resource-group my-rg \
  --issuer "$OIDC_ISSUER" \
  --subject "system:serviceaccount:default:fastapi-sa" \
  --audience "api://AzureADTokenExchange"
```

## Grant RBAC permissions

```bash
az role assignment create \
  --assignee-object-id "$MI_OBJECT_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/<vault>
```

## Kubernetes manifests

### `deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-books
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: fastapi-books
  template:
    metadata:
      labels:
        app: fastapi-books
        azure.workload.identity/use: "true" # ← required label
    spec:
      serviceAccountName: fastapi-sa # ← federated service account
      containers:
        - name: fastapi
          image: myacr.azurecr.io/fastapi-books:latest
          ports:
            - containerPort: 8000
          env:
            - name: AZURE_KEYVAULT_URL
              value: "https://myvault.vault.azure.net/"
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
```

### `service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-books-svc
spec:
  selector:
    app: fastapi-books
  ports:
    - port: 80
      targetPort: 8000
  type: ClusterIP
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-books-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-books
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

## Deploy

```bash
# Push image to ACR
az acr build --registry myacr --image fastapi-books:latest .

# Apply manifests
kubectl apply -f deployment.yaml -f service.yaml -f hpa.yaml

# Watch rollout
kubectl rollout status deployment/fastapi-books
```

## `DefaultAzureCredential` in your FastAPI code

No code change is needed. `DefaultAzureCredential` detects the Workload Identity environment variables injected by the AKS mutating webhook and uses them automatically:

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()  # ← same code as local dev and App Service
client = SecretClient("https://myvault.vault.azure.net/", credential)
```
