# MG-ERP CI/CD Workflows

This directory contains GitHub Actions workflows for the MG-ERP monorepo.

## 🔄 Workflow Structure

### Per-Service Workflows
Each service has its own dedicated CI/CD pipeline that triggers **only when files in that service change**:

- **`auth-service.yml`** - Auth service backend (port 8004)
- **`ledger-service.yml`** - Ledger service backend (port 8001)
- **`inventory-service.yml`** - Inventory service backend (port 8002)
- **`pos-service.yml`** - POS service backend (port 8003)

### Shared Workflows
- **`frontend-ci.yml`** - All frontend applications (React + TypeScript)
- **`integration-tests.yml`** - Cross-service integration tests

## 🚀 Pipeline Stages

Each service workflow includes:

1. **Test** - Run unit tests with pytest
2. **Lint** - Code quality checks (flake8, black, isort)
3. **Build** - Create Docker image and push to GitHub Container Registry
4. **Deploy Staging** - Auto-deploy to staging on `develop` branch
5. **Deploy Production** - Auto-deploy to production on `main` branch

## 📦 Docker Images

Images are published to GitHub Container Registry:
- `ghcr.io/khaaliid/mg-erp/mg-auth:latest`
- `ghcr.io/khaaliid/mg-erp/mg-ledger:latest`
- `ghcr.io/khaaliid/mg-erp/mg-inventory:latest`
- `ghcr.io/khaaliid/mg-erp/mg-pos:latest`

## 🎯 Path-Based Triggering

Workflows use path filters to run only when relevant files change:

```yaml
on:
  push:
    paths:
      - 'auth/**'
      - '.github/workflows/auth-service.yml'
```

This ensures:
- ✅ Fast CI runs (only affected services)
- ✅ Reduced CI costs
- ✅ Clear change tracking

## 🔐 Required Secrets

Configure these in GitHub repo settings:

- `GITHUB_TOKEN` - Automatically provided (for GHCR)
- Add deployment secrets per environment:
  - `STAGING_*` - Staging environment credentials
  - `PRODUCTION_*` - Production environment credentials

## 📊 Code Coverage

Coverage reports are uploaded to Codecov:
- Auth: `auth-service` flag
- Ledger: `ledger-service` flag
- Inventory: `inventory-service` flag
- POS: `pos-service` flag

## 🌍 Environments

Configure environments in GitHub:
1. **staging** - Auto-deploy from `develop` branch
2. **production** - Auto-deploy from `main` branch (with approval)

## 🛠️ Local Testing

Test workflows locally using [act](https://github.com/nektos/act):

```bash
# Test auth service workflow
act -W .github/workflows/auth-service.yml

# Test integration tests
act -W .github/workflows/integration-tests.yml
```

## 📝 Adding a New Service

1. Copy an existing service workflow (e.g., `auth-service.yml`)
2. Update service name, paths, and ports
3. Create corresponding Dockerfile in service directory
4. Add service to `integration-tests.yml`
5. Update this README

## 🔗 Related Documentation

- [Main README](../../README.md)
- [SWAGGER Documentation](../../SWAGGER_DOCUMENTATION.md)
- [Auth Service Docs](../../auth/README.md)
- [Ledger Service Docs](../../ledger/README.md)
