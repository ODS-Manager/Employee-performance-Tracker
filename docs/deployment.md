# Deployment Guide

## Prerequisites

1. **Google Cloud Project Setup**
   - Project ID: `project-0990a5d7-310c-4a56-837`
   - Region: `asia-south1` (Mumbai)
   - Artifact Registry: `ods-repo`

2. **Service Account**
   - Service Account: `github-actions@project-0990a5d7-310c-4a56-837.iam.gserviceaccount.com`
   - Workload Identity Pool: `github-actions-pool`
   - OIDC Provider: `github-provider`

## GitHub Repository Secrets

Add the following secrets in your GitHub repository (`ODS-Manager/Employee-performance-Tracker`):

```
WIF_PROVIDER = projects/302004244593/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider
SERVICE_ACCOUNT = github-actions@project-0990a5d7-310c-4a56-837.iam.gserviceaccount.com
PROJECT_ID = project-0990a5d7-310c-4a56-837
```

## Deployment Process

### 1. Automatic Deployment (Recommended)

Push to `main` branch to trigger the GitHub Actions workflow:

1. GitHub Actions authenticates using Workload Identity Federation
2. Builds Docker image and pushes to Artifact Registry
3. Deploys to Cloud Run

### 2. Manual Deployment

You can also trigger the workflow manually:
1. Go to Actions tab in GitHub
2. Select "Deploy to Cloud Run" workflow
3. Click "Run workflow"

## Docker Configuration

- **Base Image**: Python 3.11 slim
- **Port**: 8080 (Cloud Run standard)
- **Health Check**: `/health` endpoint
- **User**: Non-root user for security

## Cloud Run Configuration

- **Service Name**: `employee-performance-api`
- **Memory**: 512Mi
- **CPU**: 1
- **Min Instances**: 0 (scale to zero)
- **Max Instances**: 10
- **Authentication**: Public access enabled

## Environment Variables

The application uses the following environment variables:
- `PORT=8080` (set by Cloud Run)
- Database connection strings (to be configured in Cloud SQL)
- Redis connection (to be configured with Memorystore)

## Next Steps

After initial deployment:

1. **Database Setup**
   - Configure Cloud SQL PostgreSQL
   - Update connection strings in Secret Manager
   - Run database migrations

2. **Redis Setup**
   - Configure Memorystore Redis
   - Update connection configuration

3. **Monitoring**
   - Set up Cloud Monitoring
   - Configure logging and alerts

4. **Frontend Deployment**
   - Deploy frontend to Firebase Hosting or Cloud Storage
   - Update API endpoints to production URL

## Verification

After deployment, verify the service is running:
```bash
curl https://employee-performance-api-<hash>-a.a.run.app/health
```

The service should return: `{"status": "healthy"}`

## Troubleshooting

1. **Build Failures**: Check Dockerfile and requirements.txt
2. **Deployment Failures**: Verify service account permissions
3. **Health Check Failures**: Ensure `/health` endpoint is accessible
4. **Authentication Issues**: Verify GitHub secrets and WIF configuration
