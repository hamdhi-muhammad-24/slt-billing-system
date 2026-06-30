# Manual Setup Steps — Phase 6C/6E (AWS + GitHub)

Follow these steps IN ORDER. Each step tells you exactly what to do.
When you finish all steps, start a new chat and say: "Phase 6C is done, let's continue with Phase 6F."

---

## STEP 1 — Create a GitHub account and repository (10 min)

1. Go to https://github.com and create a free account if you don't have one.
2. Click the **+** button (top right) → **New repository**
3. Set:
   - Repository name: `slt-billing-system`
   - Visibility: **Private**
   - Do NOT tick "Add README"
4. Click **Create repository**
5. GitHub shows you commands. Run these in your project folder (PowerShell):

```powershell
cd "e:\Projects\SLT-Billing-System"
git remote add origin https://github.com/YOUR_USERNAME/slt-billing-system.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

---

## STEP 2 — Install AWS CLI (5 min)

1. Open this link: https://aws.amazon.com/cli/
2. Click **Download AWS CLI for Windows**
3. Run the downloaded `.msi` installer, click through defaults
4. Open a NEW PowerShell window (close and reopen)
5. Verify it worked:
```powershell
aws --version
```
You should see something like `aws-cli/2.x.x`

---

## STEP 3 — Create an IAM user for deployments (10 min)

1. Go to https://console.aws.amazon.com → sign in
2. Search for **IAM** in the search bar → click it
3. Left menu → **Users** → **Create user**
4. Username: `slt-deploy` → click **Next**
5. Select **Attach policies directly**
6. Search for `AdministratorAccess` → tick it → click **Next** → **Create user**
7. Click on the new user `slt-deploy`
8. Tab: **Security credentials** → **Create access key**
9. Choose **Command Line Interface (CLI)** → tick the confirmation checkbox → **Next** → **Create access key**
10. **IMPORTANT:** Copy both values now — you won't see the secret again:
    - Access key ID: `AKIA...`
    - Secret access key: `...`

---

## STEP 4 — Configure AWS CLI (2 min)

Run in PowerShell:
```powershell
aws configure
```
Enter when prompted:
- AWS Access Key ID: (paste the key from Step 3)
- AWS Secret Access Key: (paste the secret from Step 3)
- Default region name: `ap-southeast-1`
- Default output format: `json`

Verify it works:
```powershell
aws sts get-caller-identity
```
You should see your account ID and user info.

---

## STEP 5 — Create ECR repositories (3 min)

Run in PowerShell:
```powershell
aws ecr create-repository --repository-name slt-backend --region ap-southeast-1
aws ecr create-repository --repository-name slt-frontend --region ap-southeast-1
```

Copy the `repositoryUri` values from both outputs — you'll need them later.
They look like: `123456789012.dkr.ecr.ap-southeast-1.amazonaws.com/slt-backend`

---

## STEP 6 — Create S3 bucket for PDFs (3 min)

Run in PowerShell (replace `YOUR_ACCOUNT_ID` with your 12-digit AWS account ID):
```powershell
aws s3 mb s3://slt-bill-pdfs-prod --region ap-southeast-1
aws s3api put-bucket-versioning --bucket slt-bill-pdfs-prod --versioning-configuration Status=Enabled
```

---

## STEP 7 — Create RDS PostgreSQL database (15 min)

1. Go to AWS Console → search **RDS** → click it
2. Click **Create database**
3. Choose:
   - Engine: **PostgreSQL**
   - Version: PostgreSQL 16
   - Template: **Free tier** (for testing) or **Production** (for real)
   - DB instance identifier: `slt-billing-db`
   - Master username: `postgres`
   - Master password: (make a strong password, save it!)
   - Instance: `db.t3.micro`
   - Storage: 20 GB
   - **Public access: Yes** (for initial setup — we'll restrict later)
4. Click **Create database** — takes about 5 minutes
5. When created, click on the DB → copy the **Endpoint** (looks like `slt-billing-db.xxxx.ap-southeast-1.rds.amazonaws.com`)

---

## STEP 8 — Create ElastiCache Redis (10 min)

1. Go to AWS Console → search **ElastiCache** → click it
2. Click **Create cluster** → **Redis OSS**
3. Set:
   - Cluster name: `slt-redis`
   - Node type: `cache.t3.micro`
   - Number of replicas: 0 (1 node only)
4. Click **Next** through remaining screens → **Create**
5. When created, copy the **Primary endpoint** (looks like `slt-redis.xxxx.cfg.ap-southeast-1.cache.amazonaws.com:6379`)

---

## STEP 9 — Create AWS Secrets Manager entries (10 min)

Run each command in PowerShell. Replace the values in quotes with your real values:

```powershell
# Database URL (use your RDS endpoint from Step 7)
aws secretsmanager create-secret --name slt/database_url \
  --secret-string "postgresql://postgres:YOUR_DB_PASSWORD@YOUR_RDS_ENDPOINT:5432/slt_ebill" \
  --region ap-southeast-1

# JWT Secret (generate a random one)
aws secretsmanager create-secret --name slt/jwt_secret \
  --secret-string "PASTE_64_RANDOM_CHARACTERS_HERE" \
  --region ap-southeast-1

# PDF Token Secret
aws secretsmanager create-secret --name slt/pdf_token_secret \
  --secret-string "PASTE_64_RANDOM_CHARACTERS_HERE" \
  --region ap-southeast-1

# Redis URL (use your ElastiCache endpoint from Step 8)
aws secretsmanager create-secret --name slt/redis_url \
  --secret-string "redis://YOUR_REDIS_ENDPOINT:6379/0" \
  --region ap-southeast-1

aws secretsmanager create-secret --name slt/redis_url_1 \
  --secret-string "redis://YOUR_REDIS_ENDPOINT:6379/1" \
  --region ap-southeast-1

# Email
aws secretsmanager create-secret --name slt/email_from \
  --secret-string "SLT Billing <billing@yourdomain.com>" \
  --region ap-southeast-1
```

To generate a random 64-char secret, run:
```powershell
-join ((65..90 + 97..122 + 48..57) * 10 | Get-Random -Count 64 | ForEach-Object {[char]$_})
```

---

## STEP 10 — Create IAM roles for ECS (10 min)

Run in PowerShell:
```powershell
# Create the ECS task execution role (allows ECS to pull images + read secrets)
aws iam create-role --role-name ecsTaskExecutionRole \
  --assume-role-policy-document '{
    "Version":"2012-10-17",
    "Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]
  }'

aws iam attach-role-policy --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

aws iam attach-role-policy --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite

# Create the task role (allows the app itself to call S3, SES, etc.)
aws iam create-role --role-name slt-task-role \
  --assume-role-policy-document '{
    "Version":"2012-10-17",
    "Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]
  }'

aws iam attach-role-policy --role-name slt-task-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-role-policy --role-name slt-task-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonSESFullAccess
```

---

## STEP 11 — Create ECS Cluster (2 min)

```powershell
aws ecs create-cluster --cluster-name slt-cluster --region ap-southeast-1
```

---

## STEP 12 — Create CloudWatch Log Groups (1 min)

```powershell
aws logs create-log-group --log-group-name /ecs/slt-backend --region ap-southeast-1
aws logs create-log-group --log-group-name /ecs/slt-worker  --region ap-southeast-1
aws logs create-log-group --log-group-name /ecs/slt-beat    --region ap-southeast-1
```

---

## STEP 13 — Update task definition files with your Account ID (2 min)

Find your 12-digit AWS Account ID:
```powershell
aws sts get-caller-identity --query Account --output text
```

Then open these 3 files in VS Code and replace every `ACCOUNT_ID` with your real number:
- `aws/task-def-backend.json`
- `aws/task-def-worker.json`
- `aws/task-def-beat.json`

Also replace `YOUR_DOMAIN_HERE` in `task-def-backend.json` with your domain (or use `*` for now).

---

## STEP 14 — Register ECS task definitions (1 min)

```powershell
aws ecs register-task-definition --cli-input-json file://aws/task-def-backend.json --region ap-southeast-1
aws ecs register-task-definition --cli-input-json file://aws/task-def-worker.json  --region ap-southeast-1
aws ecs register-task-definition --cli-input-json file://aws/task-def-beat.json    --region ap-southeast-1
```

---

## STEP 15 — Add GitHub Actions secrets (5 min)

1. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** for each:

| Secret name | Value |
|-------------|-------|
| `AWS_ACCESS_KEY_ID` | Your IAM key from Step 3 |
| `AWS_SECRET_ACCESS_KEY` | Your IAM secret from Step 3 |
| `VITE_API_BASE_URL` | `https://YOUR_ALB_DNS_NAME` (get this from AWS after creating ALB) |

---

## STEP 16 — Run database migrations on RDS (5 min)

Run from your project folder (make sure `.env` has the RDS `DATABASE_URL`):
```powershell
alembic upgrade head
```

Or from inside Docker:
```powershell
docker build -t slt-backend .
docker run --rm -e DATABASE_URL="postgresql://postgres:PASSWORD@RDS_ENDPOINT:5432/slt_ebill" slt-backend alembic upgrade head
```

---

## ✅ When all steps are done

Start a new chat and say:
> "Phase 6C is complete. Let me know what's next — Phase 6E (DNS/SSL) and Phase 6F (monitoring)."

Claude will then create the ALB, CloudFront distribution, and CloudWatch alarms.
