# Phase 6E-6G Production Deployment Guide

Project: SLT Billing System / Automated SLT eBill Generation System  
Region: `ap-southeast-1`  
Account: `757905896932`

## 1. What is already ready

- Backend, frontend, auth, billing, PDFs, Celery, Redis, notifications, Dockerfiles, and CI/CD basics are already built.
- ECR repositories exist: `slt-backend`, `slt-frontend`.
- RDS, ElastiCache Redis, PDF S3 bucket, Secrets Manager entries, IAM roles, ECS cluster, CloudWatch log groups, and task definitions already exist.
- RDS migrations are already at Alembic head: `d9e8f7a6b5c4`.

## 2. What was missing

- ALB, target group, and listener setup.
- ECS services for backend, worker, and beat.
- Frontend production S3 bucket.
- CloudFront distribution for the React app and API routes.
- GitHub Actions deploy support for S3/CloudFront.
- CloudWatch alarms and dashboard.
- Go-live smoke-test script and checklist.

## 3. Safest next step

Commit and push these deployment automation files first. The first GitHub Actions run can safely push the backend image even if ECS services do not exist yet.

Then run the Phase 6E script locally from PowerShell. It creates or updates the missing AWS resources and prints the GitHub secrets you need to add.

## 4. First small implementation chunk

Chunk 1 is complete in the repo:

- `aws/phase-6e-deploy-infra.ps1`
- `aws/phase-6f-monitoring.ps1`
- `aws/phase-6g-smoke-test.ps1`
- `.github/workflows/deploy.yml`
- ECS task definition safety fixes

## 5. Commands to run now

Run these from PowerShell:

```powershell
cd "E:\Projects\SLT-Billing-System"
git status --short
git add .github\workflows\deploy.yml aws\task-def-backend.json aws\task-def-worker.json aws\phase-6e-deploy-infra.ps1 aws\phase-6f-monitoring.ps1 aws\phase-6g-smoke-test.ps1 aws\PHASE_6E_6G_GUIDE.md
git commit -m "Add production AWS deployment automation"
git push origin main
```

After the push, GitHub Actions should build and push the backend image. If ECS services are not created yet, the workflow will skip those deploy steps instead of failing.

## 6. Run Phase 6E

Run:

```powershell
cd "E:\Projects\SLT-Billing-System"
powershell -ExecutionPolicy Bypass -File .\aws\phase-6e-deploy-infra.ps1
```

The script will:

- Create security groups for ALB and ECS tasks if missing.
- Allow ALB to reach backend tasks on port `8000`.
- Try to allow ECS tasks to reach RDS on `5432` and Redis on `6379`.
- Create ALB, target group, and HTTP listener.
- Register the current ECS task definition JSON files.
- Create or update ECS backend, worker, and beat services.
- Create private frontend S3 bucket.
- Create CloudFront distribution with S3 as default origin and ALB as API origin.

If your RDS/Redis are not in the default VPC, stop and run this instead with your real VPC and subnet IDs:

```powershell
powershell -ExecutionPolicy Bypass -File .\aws\phase-6e-deploy-infra.ps1 -VpcId vpc-xxxxxxxx -SubnetIds subnet-aaaaaaa,subnet-bbbbbbb
```

## 7. Manual GitHub secret step

When Phase 6E finishes, it prints:

- `FRONTEND_BUCKET`
- `CLOUDFRONT_DISTRIBUTION_ID`
- `VITE_API_BASE_URL`

Add them in GitHub:

1. Open your GitHub repository.
2. Go to Settings.
3. Go to Secrets and variables.
4. Open Actions.
5. Click New repository secret.
6. Add each printed value exactly.

Do not paste AWS secret access keys, database passwords, JWT secrets, or PDF token secrets into chat.

After adding the secrets, rerun the workflow:

```powershell
git commit --allow-empty -m "Trigger production deploy"
git push origin main
```

## 8. Run Phase 6F monitoring

Without email alerts:

```powershell
cd "E:\Projects\SLT-Billing-System"
powershell -ExecutionPolicy Bypass -File .\aws\phase-6f-monitoring.ps1
```

With email alerts:

```powershell
cd "E:\Projects\SLT-Billing-System"
powershell -ExecutionPolicy Bypass -File .\aws\phase-6f-monitoring.ps1 -AlertEmail "you@example.com"
```

If you use `-AlertEmail`, AWS sends a confirmation email. Open it and confirm the SNS subscription.

## 9. Run Phase 6G smoke test

Use the `VITE_API_BASE_URL` value printed by Phase 6E:

```powershell
cd "E:\Projects\SLT-Billing-System"
powershell -ExecutionPolicy Bypass -File .\aws\phase-6g-smoke-test.ps1 -BaseUrl "https://YOUR_CLOUDFRONT_DOMAIN"
```

To test login too:

```powershell
powershell -ExecutionPolicy Bypass -File .\aws\phase-6g-smoke-test.ps1 -BaseUrl "https://YOUR_CLOUDFRONT_DOMAIN" -AdminEmail "admin@example.com" -AdminPassword "YOUR_PASSWORD"
```

Do not send the real admin password in chat.

## 10. Go-live checklist

- GitHub Actions backend image build succeeded.
- Phase 6E script completed.
- GitHub secrets are set: `FRONTEND_BUCKET`, `CLOUDFRONT_DISTRIBUTION_ID`, `VITE_API_BASE_URL`.
- GitHub Actions frontend S3 sync and CloudFront invalidation succeeded.
- CloudFront status is Deployed.
- `https://YOUR_CLOUDFRONT_DOMAIN/health` returns `{"status":"ok","db":"reachable"}`.
- React app loads from CloudFront.
- Admin login works.
- Customer login works.
- One bill generation works.
- Batch bill generation works.
- PDF download works.
- PDF object exists in `slt-bill-pdfs-prod`.
- Notification task runs without worker errors.
- CloudWatch log groups show healthy logs: `/ecs/slt-backend`, `/ecs/slt-worker`, `/ecs/slt-beat`.
- CloudWatch dashboard exists: `slt-billing-production`.
- Alarms exist for ECS, ALB, RDS, and Redis where available.

## 11. Optional custom domain and SSL

The default setup uses CloudFront HTTPS, so it works without buying a domain.

If you later use a custom domain:

- Request an ACM certificate for CloudFront in `us-east-1`.
- Validate it in DNS.
- Re-run Phase 6E with `-DomainName "billing.example.com"` and `-CertificateArn "arn:aws:acm:us-east-1:..."`.
- Create a DNS CNAME or Route 53 alias from the domain to the CloudFront distribution.
