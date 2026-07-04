# IMPLEMENTATION DETAILS & DEPLOYMENT GUIDES

## PART 1: TECHNOLOGY CHOICES EXPLAINED

### Backend Stack Justification

#### Why Python + FastAPI?

**Python Advantages:**
```
✅ Financial domain libraries: Decimal for exact arithmetic
✅ Data science ecosystem: pandas, numpy for analytics
✅ Readability: Clear code, fewer bugs, faster development
✅ Async support: FastAPI has native async/await
✅ Ecosystem: 300k+ packages on PyPI
✅ Learning curve: Easier for new developers
```

**FastAPI Advantages:**
```
✅ Performance: 100k+ requests/second (comparable to Node.js)
✅ Auto-docs: Swagger UI automatically generated
✅ Type hints: Full type safety with Pydantic v2
✅ Async-first: Built for modern async Python
✅ Validation: Automatic request/response validation
✅ Community: Growing rapidly, active development
```

**Alternatives Considered:**
| Framework | Pros | Cons |
|-----------|------|------|
| **Node.js/Express** | Fast, huge ecosystem | Money = float (rounding errors), less ORM maturity |
| **Django** | Batteries-included, ORM | Older, slower dev, over-featured for API |
| **Go/Rust** | Ultra-fast, compiled | Steep learning curve, smaller ecosystem |
| **Java/Spring** | Enterprise-grade | Verbose, slower startup, resource-hungry |

**Verdict:** FastAPI is **modern, fast, and perfect for REST APIs with strict data validation**.

---

#### Why PostgreSQL over MySQL/MongoDB?

**PostgreSQL Strengths:**
```
🏆 Money types: NUMERIC(12,2) - exact arithmetic, no float rounding
🏆 Constraints: Foreign keys, unique constraints, check constraints
🏆 Transactions: Full ACID support for financial data
🏆 JSON support: Can store nested data if needed
🏆 Performance: Optimized for read-heavy workloads (billing queries)
🏆 Ecosystem: Best SQLAlchemy support, Alembic migrations
```

**Real Example - Why MySQL fails:**
```python
# MySQL
SELECT 7703.28 - 5000.00  # Returns: 2703.28000000001 (float math!)

# PostgreSQL
SELECT NUMERIC '7703.28' - NUMERIC '5000.00'  # Returns: 2703.28 (exact!)
```

**MongoDB Rejection:**
```
❌ No decimal type (uses float64)
❌ Weak constraints (referential integrity optional)
❌ Complex queries hard (billing queries need joins)
❌ Transactions limited until v4.0, still weak
✅ Good for: flexible schemas, horizontal scaling
✗ Bad for: financial data, reports, complex queries
```

**Verdict:** PostgreSQL is **the gold standard for financial applications**.

---

#### Why Redis for Celery?

**Redis Advantages:**
```
⚡ Ultra-fast: In-memory, sub-millisecond latency
📦 Simple: Single-node setup, minimal configuration
🔒 Reliable: AOF persistence (survives crashes)
📡 Compatible: Standard Celery/RabbitMQ alternative
💰 Cost-effective: Cheaper than RabbitMQ, easier to operate
🚀 Scalable: ElastiCache in AWS, built-in clustering
```

**Alternatives:**
| Broker | Speed | Reliability | Ops Complexity | Cost |
|--------|-------|-------------|----------------|------|
| **Redis** | ⚡ Super fast | Reliable (AOF) | ✅ Simple | $ Low |
| **RabbitMQ** | ⚡ Fast | Very reliable | ⚠️ Complex | $$ Medium |
| **SQS (AWS)** | ⏱️ Slower | Very reliable | ✅ Simple | $$$ Higher |
| **Kafka** | ⚡ Fast | Very reliable | ❌ Complex | $$$ Higher |

**Verdict:** Redis provides **the best balance of speed, simplicity, and cost for Celery**.

---

### Frontend Stack Justification

#### Why React + TypeScript?

**React Advantages:**
```
✅ Component model: Reusable, composable UIs
✅ Virtual DOM: Efficient updates
✅ Ecosystem: 50k+ packages, huge community
✅ Jobs: Most sought-after frontend skill
✅ Learning: Clear mental model, documentation
✅ Scalability: Scales from 10k to 10M users
```

**TypeScript Advantages:**
```
🛡️ Type safety: Catch errors at compile-time
📖 Documentation: Types serve as inline docs
🚀 Developer experience: IDE autocomplete, refactoring
🐛 Fewer bugs: ~15% fewer bugs in production
🧪 Testability: Easier to test typed code
```

**Alternatives:**
| Framework | Popularity | Learning | Ecosystem | Typing |
|-----------|-----------|----------|-----------|--------|
| **React** | ⭐⭐⭐⭐⭐ | Medium | Massive | ✅ TS |
| **Vue** | ⭐⭐⭐⭐ | Easy | Medium | ✅ TS |
| **Angular** | ⭐⭐⭐ | Hard | Large | ✅ TS |
| **Svelte** | ⭐⭐⭐ | Easy | Small | ✅ TS |

**Verdict:** React + TypeScript is **the industry standard for production web apps**.

---

#### Why Vite over Webpack?

**Vite Advantages:**
```
🚀 Build speed: 10-100x faster than Webpack
🔥 Dev experience: Instant hot module reloading
📦 Modern: ESM-native, no complex configuration
⚡ Optimized output: Tree-shaking, code splitting
🧹 Zero config: Works out-of-box
```

**Real Numbers:**
```
Webpack: npm run dev takes 20-30 seconds
Vite:    npm run dev takes 100-200ms ✅

Webpack: Full rebuild on change: 5-10 seconds
Vite:    Hot reload: 50-100ms ✅
```

**Verdict:** Vite is the **modern choice for React development** (Webpack is legacy).

---

### AWS Services Selection

#### Why ECS Fargate (not EC2/Lambda)?

**ECS Fargate Advantages:**
```
✅ No server management: AWS handles scaling, patching
✅ Cost-effective: Pay per CPU/memory second used
✅ Containers: Portable, reproducible deployments
✅ Scaling: Auto-scale based on metrics
✅ Integration: Works with ALB, RDS, ElastiCache
✅ Complexity: Sweet spot between Lambda and EC2
```

**Alternatives:**
| Platform | Scaling | Cost | Operations | Best For |
|----------|---------|------|-----------|----------|
| **Fargate** | Auto | Moderate | ✅ Easy | APIs, services |
| **Lambda** | Auto | Low | ✅ Very easy | Serverless, FaaS |
| **EC2** | Manual | Lowest | ❌ Complex | Full control |
| **Kubernetes** | Auto | Varies | ❌ Very complex | Large teams |

**Why NOT Lambda:**
```
❌ 15-minute timeout (our billing run takes 30 min)
❌ Cold start (bad for API) 
✅ Good for: one-time functions, webhooks, scheduled tasks
```

**Why NOT full Kubernetes:**
```
❌ Overkill for current scale (10,000 accounts)
❌ Steep learning curve
❌ More expensive to operate
✅ Good for: 100k+ accounts, multi-team coordination
```

**Verdict:** ECS Fargate is **perfect for this scale and team size**.

---

#### Why RDS (not DynamoDB)?

**RDS Advantages:**
```
🏆 SQL: Complex queries, joins, aggregations
🏆 ACID: Full transaction support
🏆 Constraints: Foreign keys, unique, check
🏆 Backup: Automated, point-in-time recovery
🏆 Scaling: Vertical (larger instances) + read replicas
```

**DynamoDB Use Cases:**
```
✅ Good for: High-frequency writes, real-time IoT
✗ Bad for: Complex queries, reporting, financial data
```

**Verdict:** RDS is **the right choice for billing/financial data**.

---

#### Why CloudFront + S3 (not just S3)?

**CloudFront Benefits:**
```
🚀 Speed: 100+ edge locations globally (~100ms latency)
💰 Cost: Cheaper than S3 for high traffic
🔒 Security: DDoS protection, WAF integration
🔄 Origin: Can point to ALB (API), S3 (frontend), or both
🧠 Caching: Intelligent caching, cache invalidation
```

**S3 alone:**
```
❌ No edge caching (always travel to ap-southeast-1)
❌ Higher bandwidth costs
❌ No DDoS protection
```

**Verdict:** CloudFront is **essential for global performance**.

---

## PART 2: DEPLOYMENT STEP-BY-STEP

### Phase 6E: Infrastructure Setup

#### Step 1: Prerequisites

```bash
# 1. AWS Account setup
- Create AWS Account (if not exists)
- Create IAM user with PowerUser permissions
- Generate access keys (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
- Store securely (use AWS Secrets Manager)

# 2. GitHub setup
- Create GitHub repository
- Add AWS credentials as secrets
- Enable Actions (Settings > Actions > Allow all actions)

# 3. Local tools
- Install AWS CLI: `pip install awscli`
- Install Docker Desktop
- Install PowerShell 7+ (if on Windows)
```

#### Step 2: Run Phase 6E PowerShell Script

```powershell
# From project root
cd E:\Projects\SLT-Billing-System
powershell -ExecutionPolicy Bypass -File .\aws\phase-6e-deploy-infra.ps1

# Script does:
# 1. Create VPC security groups (ALB, ECS, RDS)
# 2. Create Application Load Balancer
# 3. Create target group + listener
# 4. Register ECS task definitions
# 5. Create ECS services (backend, worker, beat)
# 6. Create S3 bucket for frontend
# 7. Create CloudFront distribution
# 8. Output: GitHub secrets to add
```

#### Step 3: Add GitHub Secrets

```
Settings > Secrets and variables > Actions > New repository secret

AWS_ACCESS_KEY_ID: <from IAM user>
AWS_SECRET_ACCESS_KEY: <from IAM user>
AWS_REGION: ap-southeast-1
FRONTEND_BUCKET: <output from script>
CLOUDFRONT_DISTRIBUTION_ID: <output from script>
VITE_API_BASE_URL: https://<cloudfront-domain>.cloudfront.net/api
DATABASE_URL: postgresql://user:pass@rds-endpoint:5432/slt_ebill
CELERY_BROKER_URL: redis://elasticache-endpoint:6379/0
CELERY_RESULT_BACKEND: redis://elasticache-endpoint:6379/1
JWT_SECRET: <generate: openssl rand -hex 32>
```

#### Step 4: Initialize Database

```bash
# Create RDS database
aws rds create-db-instance \
  --db-instance-identifier slt-postgres \
  --db-instance-class db.t3.small \
  --engine postgres \
  --master-username postgres \
  --master-user-password <generated-password>

# Wait for creation (~5 minutes)
aws rds wait db-instance-available --db-instance-identifier slt-postgres

# Get endpoint
aws rds describe-db-instances --db-instance-identifier slt-postgres \
  --query 'DBInstances[0].Endpoint.Address'

# Connect and run migrations
PGPASSWORD=<password> psql -h <endpoint> -U postgres -c "CREATE DATABASE slt_ebill"
alembic upgrade head --sql  # Generate SQL
psql -h <endpoint> -U postgres -d slt_ebill < migrations.sql
```

---

### Phase 6F: Monitoring Setup

#### CloudWatch Dashboard

```bash
# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name slt-system \
  --dashboard-body file://dashboard-config.json
```

#### Alarms

```bash
# CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name slt-api-cpu-high \
  --alarm-actions arn:aws:sns:ap-southeast-1:ACCOUNT:AlertTopic \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

---

### Phase 6G: Smoke Testing

```bash
# From Phase 6G script
powershell -ExecutionPolicy Bypass -File .\aws\phase-6g-smoke-test.ps1

# Tests:
# 1. Frontend loads
# 2. API is healthy (/health endpoint)
# 3. Database connected
# 4. Cache connected
# 5. Login works
# 6. Can view bills (after authentication)
# 7. PDF generation works
```

---

## PART 3: COMMON DEPLOYMENT ISSUES & FIXES

### Issue 1: "Task failed to start" in ECS

```
Error: Task exited with code 1

Solution:
1. Check logs: aws logs tail /ecs/slt-backend --follow
2. Common causes:
   - Missing environment variables → Update Secrets Manager
   - Database connection failure → Check RDS endpoint, security groups
   - Port in use → Check task definition port mapping
   - Image not found → Verify ECR image URI in task definition
3. Fix and re-deploy: git push (triggers GitHub Actions)
```

---

### Issue 2: "502 Bad Gateway" from CloudFront

```
Error: Request fails through CloudFront

Solution:
1. Test directly to ALB (bypass CloudFront):
   curl -H "Host: drfqpu3cjgoc4.cloudfront.net" \
     http://<alb-endpoint>/api/health
2. If ALB works:
   - Invalidate CloudFront cache: aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"
   - Wait 1-2 minutes for propagation
3. If ALB fails:
   - Check ECS task status: aws ecs describe-services --cluster slt-cluster --services slt-backend-service
   - Check target health: aws elbv2 describe-target-health --target-group-arn <arn>
```

---

### Issue 3: "Connection refused" from API to RDS

```
Error: FATAL: no pg_hba.conf entry

Solution:
1. Check RDS security group allows 5432 from ECS:
   aws ec2 authorize-security-group-ingress \
     --group-id sg-rds \
     --protocol tcp \
     --port 5432 \
     --source-group sg-ecs
2. Test connection:
   psql -h <rds-endpoint> -U postgres -d slt_ebill -c "SELECT 1"
3. Check database exists:
   psql -h <rds-endpoint> -U postgres -c "\\l"  # List databases
```

---

### Issue 4: Celery workers not processing jobs

```
Error: QUEUED notifications never become SENT

Solution:
1. Check Redis connection:
   redis-cli -h <elasticache-endpoint> ping  # Should return PONG
2. Check worker logs:
   aws logs tail /ecs/slt-worker --follow
3. Restart workers:
   aws ecs update-service --cluster slt-cluster \
     --service slt-worker-service --force-new-deployment
4. Check queue depth:
   redis-cli -h <endpoint> LLEN celery
```

---

### Issue 5: Notifications not sending via SES

```
Error: Notification status stays QUEUED, not SENT

Solution:
1. Check SES configuration:
   aws ses verify-email-identity --email-address support@slt.lk
   aws ses verify-domain-dkim --domain slt.lk
2. Check SES sandbox status:
   aws ses describe-configuration-set --configuration-set-name slt
   - If in sandbox, can only send to verified addresses
   - Request production access: AWS Console > SES > Sending limits
3. Check worker logs for errors:
   aws logs filter-log-events \
     --log-group-name /ecs/slt-worker \
     --filter-pattern "ERROR"
```

---

## PART 4: SCALING GUIDE

### Scaling to 50,000 Accounts

#### Database
```bash
# Upgrade RDS instance
aws rds modify-db-instance \
  --db-instance-identifier slt-postgres \
  --db-instance-class db.t3.medium \  # Larger instance
  --apply-immediately

# Add read replica (for reporting)
aws rds create-db-instance-read-replica \
  --db-instance-identifier slt-postgres-replica \
  --source-db-instance-identifier slt-postgres
```

#### ECS Services
```bash
# Increase desired count (API service)
aws ecs update-service \
  --cluster slt-cluster \
  --service slt-backend-service \
  --desired-count 4

# Set auto-scaling target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/slt-cluster/slt-backend-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10
```

#### Celery Workers
```bash
# Increase worker count
aws ecs update-service \
  --cluster slt-cluster \
  --service slt-worker-service \
  --desired-count 4  # Parallel workers

# Optimize Celery:
# - Batch size: 100 (process 100 accounts per batch)
# - Retry: exponential backoff (1s, 2s, 4s, 8s)
# - Timeout: 3600 seconds (1 hour per account max)
```

#### Redis
```bash
# Upgrade cache node
aws elasticache modify-cache-cluster \
  --cache-cluster-id slt-redis \
  --cache-node-type cache.t3.small \  # Larger node
  --apply-immediately
```

---

### Scaling to 500,000+ Accounts

#### Architecture Changes
```
Current (10k accounts):
├─ 1 RDS instance (t3.small)
├─ 2-4 ECS tasks
├─ 1 Redis instance
└─ Single CloudFront

Scaled (500k accounts):
├─ RDS cluster (writer + 3 readers, db.r5.xlarge)
├─ 10-20 ECS tasks (across 3 AZs)
├─ Redis cluster (3 shards, multi-AZ)
├─ Database sharding (partition by account_id % 10)
├─ API caching layer (Redis, TTL=1 hour)
└─ CloudFront with origin groups
```

#### Implementation
```bash
# 1. Switch to RDS Aurora (serverless v2)
# 2. Enable read-only replicas for reporting
# 3. Implement database sharding (Citus or manual)
# 4. Add Redis cluster (replaces single node)
# 5. Increase ECS desired count to 10-20
# 6. Split workers: 5 for billing, 5 for notifications
# 7. Add API caching middleware
# 8. Implement rate limiting (100 req/sec per user)
```

---

## PART 5: COST OPTIMIZATION

### Current Cost (~$189/month)

```
ECS Fargate:     $35   (3 tasks × 0.5 vCPU × 1GB)
RDS PostgreSQL:  $80   (db.t3.small, 100GB)
ElastiCache:     $15   (cache.t3.micro, 1GB)
ALB:             $20   (1 ALB, routing)
CloudFront:      $5    (low traffic)
S3:              $10   (100GB storage)
CloudWatch:      $15   (logs + metrics)
SES:             $1    (100k emails)
Misc:            $8    (rounding, tax)
─────────────────────
TOTAL:          $189/month
```

### Cost Reduction Strategies

#### Strategy 1: Reserved Instances (-40%)
```bash
# Purchase 1-year reservations
# Covers: ECS Fargate, RDS

Savings: $80/month (40% discount)
New total: $109/month
Trade-off: Less flexibility
```

#### Strategy 2: Optimize RDS
```bash
# Use db.t3.micro instead of t3.small
Savings: $20/month
New total: $169/month
Trade-off: Slower during peak (burst seconds limited)
```

#### Strategy 3: Delete Old PDFs
```bash
# Lifecycle policy: Delete PDFs after 90 days
# Keep only recent PDFs in hot storage
Savings: $3-5/month
New total: $164/month
Trade-off: No archive (use Glacier if needed)
```

#### Strategy 4: Use Spot Instances
```bash
# ECS: Use Spot for non-critical services
# RDS: No Spot available (always on-demand)
Savings: $15/month (50% of Fargate cost)
New total: $174/month
Trade-off: Interruption risk (acceptable for batch)
```

#### Strategy 5: Consolidate Services
```bash
# Run API + Worker in same task
# Only one Fargate container instead of two
Savings: $20/month (one less task)
New total: $169/month
Trade-off: Less isolation, harder to scale independently
```

**Recommended Path:**
```
Month 1-3: Current ($189/month) - focus on stability
Month 3-6: Reserved instances + optimize RDS (-$40, = $149/month)
Month 6+: Fine-tune based on actual usage patterns
```

---

## PART 6: SECURITY HARDENING

### Week 1: Access Control
```bash
# 1. Enable MFA on AWS root account
# 2. Rotate IAM access keys (monthly)
# 3. Enable CloudTrail for all API calls
# 4. Create VPC Flow Logs

aws ec2 create-flow-logs --resource-type VPC \
  --resource-ids vpc-xxxxx \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/flowlogs
```

### Week 2: Encryption
```bash
# 1. Enable RDS encryption (KMS)
# 2. Enable S3 bucket encryption
# 3. Enable CloudWatch Logs encryption
# 4. Rotate database password (AWS Secrets Manager)

aws rds modify-db-instance \
  --db-instance-identifier slt-postgres \
  --storage-encrypted \
  --kms-key-id arn:aws:kms:ap-southeast-1:ACCOUNT:key/ID
```

### Week 3: Network Hardening
```bash
# 1. Enable VPC endpoints (avoid internet for AWS APIs)
# 2. Implement WAF on CloudFront
# 3. Enable GuardDuty (threat detection)
# 4. Implement network ACLs (additional firewall)

aws waf create-web-acl --name slt-waf \
  --metric-name slt_waf_metrics \
  --default-action Type=ALLOW
```

### Week 4: Monitoring & Incident Response
```bash
# 1. Create CloudWatch alarms for suspicious activity
# 2. Set up SNS for critical alerts
# 3. Create runbook for security incidents
# 4. Schedule quarterly penetration testing
```

---

