# Complete Workflow: How I Built the SLT E-Bill System from Start to End

## Phase 0: Foundation (Database + Engine + PDF)

### Step 1: Created the Database Structure
**What I did:**
- Designed 12 database tables using PostgreSQL to store all billing data
- Used `NUMERIC(12,2)` type for all money values (prevents float rounding errors)
- Created relationships between customers, accounts, invoices, payments, line items

**Why PostgreSQL:**
- Exact decimal arithmetic (no float rounding)
- Strong constraints and relationships
- Perfect for financial data

**Tables created:**
```
customers          → Name, address, contact info
accounts           → Customer's account number, service label
invoices           → Generated bills with totals
invoice_line_items → Charges, taxes, discounts per invoice
payments           → Customer payments received
users              → Admin and customer login accounts
notification_outbox → Email/SMS delivery tracking
```

**Tools used:**
- PostgreSQL 15 (database)
- SQLAlchemy 2.x (Python ORM to interact with DB)
- Alembic (version control for database changes)

---

### Step 2: Built the Billing Engine (Core Logic)
**What I did:**
- Created pure Python functions that calculate billing totals
- Formula: `Total = (Arrears + Charges for Period)`
  - Arrears = Previous balance - Payments received
  - Charges = Sum of all line items (rentals, usage, taxes, fees)

**Why framework-independent:**
- Can test without FastAPI or web server
- Easy to reuse anywhere (CLI, batch, API)
- Easy to swap database later

**Core calculation:**
```python
def assemble_bill(inputs):
    charges_total = sum(all line items)
    payments_received = sum(payments)
    balance_bf = previous balance
    arrears = balance_bf - payments_received
    total_payable = arrears + charges_total
    return total_payable  # FROZEN snapshot, never changes
```

**Verified with real data:**
- Sample account total = **4628.52** ✅ (matches actual SLT bill)

**Tools used:**
- Python 3.11 (pure logic, no frameworks)
- Decimal type (exact money arithmetic)
- Pydantic 2.x (validates Bill object schema)

---

### Step 3: Created Invoice PDF Template (SLT Format)
**What I did:**
- Designed the visual layout matching SLT's official invoice format
- Created multi-page support (handles 50+ line items)
- Built in Sinhala/Tamil font support (Noto Sans fonts)
- Added barcode/QR code placeholder

**Layout sections:**
```
┌──────────────────────────────┐
│  SLT LOGO + HEADER           │  ← Blue banner
│  Invoice Number + Period     │
├──────────────────────────────┤
│  CUSTOMER DETAILS            │  ← Name, account, address
├──────────────────────────────┤
│  SUMMARY BOXES               │  ← Previous balance, charges, total
├──────────────────────────────┤
│  CHARGES TABLE               │  ← Grouped by service type
│  ┌─────────────┐             │
│  │ RENTAL      │ LKR 500     │
│  │ USAGE       │ LKR 3500    │
│  │ DISCOUNT    │ LKR -100    │
│  │ TAX @ 15%   │ LKR 628.52  │
│  └─────────────┘             │
├──────────────────────────────┤
│  PAYMENT SLIP (detachable)   │
│  Barcode + QR code           │
└──────────────────────────────┘
(Page 2 if many items: repeat header + continue table)
```

**Tools used:**
- ReportLab 4.1 (PDF generation library)
- Platypus (flowables for dynamic layout)
- python-barcode (barcode generation)
- qrcode (QR code generation)
- Noto Sans/Sinhala/Tamil fonts (embedded in PDF)

---

## Phase 1: REST API Layer (FastAPI)

### Step 4: Built FastAPI Backend
**What I did:**
- Created REST API with 30+ endpoints
- Connected to PostgreSQL database
- Added request/response validation
- Generated automatic Swagger documentation

**API endpoints:**
```
Customers:
  GET    /api/customers          → List all customers
  GET    /api/customers/{id}     → Get one customer details
  POST   /api/customers          → Create new customer

Accounts:
  GET    /api/accounts           → List accounts
  GET    /api/accounts/{id}      → Account details with balance

Invoices:
  GET    /api/invoices           → Paginated invoice list
  GET    /api/invoices/{id}      → Invoice summary (JSON)
  GET    /api/invoices/{id}/pdf  → Download PDF file

Billing:
  POST   /api/billing/generate   → Manually trigger billing run
  GET    /api/billing/status     → Check billing run progress
```

**Money handling in API:**
```python
# Database stores: 4628.52 (exact Decimal)
# API returns JSON: "4628.52" (string, no rounding)
# Frontend displays: "4,628.52" (formatted with commas)
```

**Why Pydantic v2:**
- Automatic validation of inputs (catches bad data early)
- Type hints (IDE autocomplete, fewer bugs)
- Auto-generated OpenAPI/Swagger docs

**Tools used:**
- FastAPI 0.111 (REST framework)
- Pydantic 2.x (data validation)
- SQLAlchemy 2.x (ORM queries)
- Python Decimal (exact money math)
- python-jose + PyJWT (JWT tokens)

---

## Phase 2: Frontend Interface (React + TypeScript)

### Step 5: Built Customer Portal
**What I did:**
- Created React components for customer to view their bills
- Customers can login with email/password
- Can view bill history and download PDFs
- Responsive design (works on phone/tablet/desktop)

**Pages:**
```
Login Page
  → Enter email + password + role selection
  
Customer Dashboard
  → Recent bills (table)
  → Download PDF button
  → View details link

Invoice Detail Page
  → Bill summary (previous balance, charges, total)
  → Charges breakdown (rental, usage, tax)
  → Payment slip info
  → Download PDF button
```

**Tools used:**
- React 19 (UI components)
- TypeScript 6 (type safety)
- Vite 8 (ultra-fast bundler)
- Tailwind CSS v4 (styling)
- shadcn/ui (pre-built components)
- React Router v7 (page navigation)
- TanStack Query v5 (fetch data from API)

---

### Step 6: Built Admin Portal
**What I did:**
- Created separate admin dashboard
- Admin can trigger billing runs manually
- Admin can see customer list with account info
- Admin can monitor billing job status
- Admin can view notification delivery history

**Pages:**
```
Admin Dashboard
  → Stats (total accounts, pending bills, sent notifications)
  → Trigger Manual Billing button
  → Customers table (searchable, sortable)
  → Customer details (all accounts, payment history)

Billing Status
  → Current run progress (X of 1000 accounts processed)
  → Failures (which accounts failed, why)
  → Retry failed accounts

Notification History
  → Email sent to john@example.com ✓
  → SMS sent to +94777123456 ✓
  → Failed: invalid_email@invalid ✗
```

**Tools used:**
- Same as customer portal (React, TypeScript, etc.)
- Additional: shadcn/ui Charts (visual dashboards)

---

## Phase 3: Authentication & Authorization

### Step 7: Added JWT Login System
**What I did:**
- Created JWT token-based authentication
- Support for two roles: ADMIN and CUSTOMER
- Password hashing with bcrypt (secure)
- Token expiry (60 minutes for security)

**How it works:**
```
1. User enters email + password → POST /auth/login
2. API checks password hash matches DB
3. If correct → Generate JWT token (contains user_id, role)
4. Frontend stores token in localStorage
5. All future requests include token in header: 
   Authorization: Bearer eyJhbGc...
6. API verifies token is valid + not expired
7. If expired → Force login again
```

**Database:**
```
users table:
  id, email, password_hash (bcrypt), role (ADMIN/CUSTOMER), is_active

customers table:
  id, user_id (FK), name, address, ...
  (one customer per user)
```

**Tools used:**
- PyJWT 2.8 (create/verify JWT tokens)
- passlib + bcrypt (secure password hashing)
- FastAPI dependencies (inject current user into routes)

---

## Phase 4: Automation with Scheduler (Celery + Redis)

### Step 8: Built Monthly Billing Automation
**What I did:**
- Set up Celery to run billing automatically on 1st of every month at midnight
- Celery workers process accounts in parallel (faster)
- Redis broker coordinates jobs between workers

**How it works:**
```
Month 1 (Jan 1, 00:00):
├─ Trigger: Celery Beat scheduler (cron: "0 0 1 * *")
├─ Task: run_monthly_billing()
│
├─ Worker 1: Process accounts 1-250
├─ Worker 2: Process accounts 251-500
├─ Worker 3: Process accounts 501-750
├─ Worker 4: Process accounts 751-1000
│
├─ For each account:
│   ├─ Query database (charges, payments)
│   ├─ Run billing engine
│   ├─ Generate PDF
│   ├─ Store invoice in database
│   └─ Add to notification queue
│
├─ Handle failures:
│   ├─ If account fails → Log error + continue
│   ├─ Store in billing_run_failures table
│   └─ Admin can retry manually later
│
└─ Result: 1000 invoices generated in ~30 minutes
```

**Redis role:**
- Stores job queue
- Tracks which accounts completed
- Allows parallel workers to coordinate

**Flower monitoring:**
- Web UI to see running jobs
- See which workers are active
- Track job completion percentage

**Tools used:**
- Celery 5.3 (distributed task queue)
- Celery Beat (scheduler)
- Redis 7 (message broker)
- Flower (monitoring dashboard)

---

## Phase 5: Notifications (Email + SMS)

### Step 9: Added Email/SMS Delivery
**What I did:**
- After each bill is generated, send notification to customer
- Email includes bill summary + PDF attachment
- SMS is optional (text message with link to download)
- Track delivery status (sent, failed, bounced)

**How it works:**
```
1. Billing engine creates invoice
2. Notification task added to queue
   
3. Worker checks notification_outbox table
   ├─ Status: QUEUED (waiting to send)
   ├─ Channel: EMAIL or SMS
   ├─ Recipient: john@example.com or +94777123456
   
4. Worker sends:
   
   EMAIL:
   ├─ Use AWS SES (production) or SMTP (local dev)
   ├─ Subject: "Your SLT Bill - January 2026"
   ├─ Body: HTML template with charges table
   ├─ Attachment: invoice.pdf
   └─ Record provider_ref (SES message ID)
   
   SMS:
   ├─ Use AWS SNS (production) or Twilio (local dev)
   ├─ Message: "Your bill is ready. Download: https://..."
   ├─ Send via WhatsApp optional
   └─ Record provider_ref (SMS ID)

5. Update notification_outbox status:
   ├─ If success → status = SENT
   ├─ If fail → status = FAILED, record error
   └─ If bounce → status = FAILED, record bounce reason

6. Idempotent (never send twice):
   ├─ Unique constraint: (invoice_id, channel)
   ├─ Even if worker crashes → retry continues from where it left
```

**Outbox Pattern (reliability):**
- Store notifications in database first (transaction with invoice)
- Worker scans database for QUEUED notifications
- Guaranteed delivery (if worker crashes, retry on restart)
- No notifications get lost

**Tools used:**
- AWS SES (production email)
- AWS SNS (production SMS)
- SMTP (local development email)
- Twilio (local development SMS)
- Jinja2 (HTML email templates)
- python-email (attach PDF to email)

---

## Phase 6A-6D: Cloud Preparation (Docker + GitHub Actions)

### Step 10: Containerized Everything
**What I did:**
- Created Dockerfile to package entire app
- Created docker-compose.yml for local development
- Set up GitHub Actions for automated builds

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app
COPY migrations/ ./migrations

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml:**
```yaml
services:
  redis:
    image: redis:7-alpine
    ports: [6379:6379]
    
  mailpit:
    image: mailpit:latest
    ports: [1025:1025, 8025:8025]  # SMTP + UI
```

**GitHub Actions Workflow:**
```yaml
on: [push to main]

steps:
  1. Checkout code
  2. Login to AWS ECR
  3. Build Docker image
  4. Push to ECR (container registry)
  5. Register task definition
  6. Update ECS services
```

**Tools used:**
- Docker (containerization)
- GitHub Actions (CI/CD pipeline)
- AWS ECR (container registry)

---

## Phase 6E: AWS Infrastructure Setup

### Step 11: Deployed to Production (AWS)
**What I did:**
- Created AWS infrastructure using PowerShell script
- Database: RDS PostgreSQL (managed)
- Cache: ElastiCache Redis (managed)
- API: ECS Fargate containers (auto-scaling)
- Frontend: S3 + CloudFront CDN

**Architecture:**
```
                    ┌─────────────────────┐
                    │   CloudFront CDN    │
                    │  (global caching)   │
                    └──────────┬──────────┘
                               │
                   ┌───────────┴───────────┐
                   │                       │
            ┌──────▼────────┐    ┌────────▼──────┐
            │  S3 Bucket    │    │  ALB          │
            │ (frontend)    │    │ (load balance)│
            └───────────────┘    └────────┬──────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
            ┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼───────┐
            │  ECS Backend   │  │  ECS Worker    │  │  ECS Beat      │
            │  (API)         │  │  (Celery)      │  │  (Scheduler)   │
            │  2-4 tasks     │  │  2-4 tasks     │  │  1 task        │
            └───────┬────────┘  └────────┬────────┘  └────────┬───────┘
                    │                    │                    │
                    └────────────────────┼────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
            ┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼───────┐
            │  RDS (DB)      │  │  ElastiCache   │  │  S3 (PDFs)    │
            │  PostgreSQL    │  │  Redis         │  │  CloudWatch   │
            │  15GB storage  │  │  1GB cache     │  │  Monitoring   │
            └────────────────┘  └────────────────┘  └────────────────┘
```

**AWS Services used:**
```
Compute:
  - ECS Fargate (containerized services)
  - Application Load Balancer (traffic distribution)
  
Database:
  - RDS PostgreSQL (managed database)
  - ElastiCache Redis (managed cache)
  
Storage:
  - S3 (PDF storage, frontend hosting)
  - CloudFront CDN (global edge caching)
  
Monitoring:
  - CloudWatch Logs (application logs)
  - CloudWatch Metrics (performance monitoring)
  - CloudWatch Alarms (alerts)
  
Secrets:
  - AWS Secrets Manager (store DB password, API keys)
  
Email/SMS:
  - SES (email delivery)
  - SNS (SMS delivery)
```

**Deployment steps:**
```
1. PowerShell script creates:
   ├─ VPC + Security groups
   ├─ ALB + Target groups
   ├─ RDS PostgreSQL instance
   ├─ ElastiCache Redis
   ├─ S3 buckets
   ├─ CloudFront distribution
   ├─ ECS cluster + services
   └─ CloudWatch dashboards

2. GitHub Actions automatically:
   ├─ Builds Docker image on push
   ├─ Pushes to ECR
   ├─ Updates ECS task definition
   ├─ Deploys new version to Fargate

3. Database:
   ├─ Run Alembic migrations (schema setup)
   ├─ Seed sample data
   └─ Verify connection

4. Test:
   ├─ Health check: GET /api/health
   ├─ Login test: POST /auth/login
   ├─ Bill generation: POST /api/billing/generate
   └─ PDF download: GET /api/invoices/{id}/pdf
```

---

## Phase 6F: Monitoring & Alerts

### Step 12: Set Up Monitoring
**What I did:**
- Created CloudWatch dashboard
- Set up alerts for critical issues
- Monitored CPU, memory, error rates

**Dashboard shows:**
```
Real-time metrics:
  ├─ API response time (average, p95, p99)
  ├─ CPU usage (should be < 70%)
  ├─ Memory usage (should be < 80%)
  ├─ Error rate (should be < 1%)
  ├─ Active database connections
  ├─ Redis hit rate (cache efficiency)
  └─ Celery queue depth (pending jobs)

Alerts trigger if:
  ├─ CPU > 80% for 5 minutes → Scale up ECS
  ├─ Error rate > 5% → Page on-call engineer
  ├─ API latency > 2000ms → Investigate database
  ├─ Database connections > 20 → Connection leak
  ├─ Redis memory > 90% → Increase cache size
  └─ Celery queue > 1000 → More workers needed
```

**Tools used:**
- CloudWatch Logs (centralized logging)
- CloudWatch Metrics (performance data)
- CloudWatch Alarms (automated alerts)
- SNS (send alerts via email/SMS)

---

## Phase 6G: Production Validation (Smoke Tests)

### Step 13: Verified Everything Works
**What I did:**
- Created automated test suite
- Tests run every day to verify production is healthy
- PowerShell script checks critical paths

**Smoke tests:**
```
1. Frontend loads
   GET https://drfqpu3cjgoc4.cloudfront.net
   Verify: Page title "SLT e-Bill"

2. API health
   GET /api/health
   Verify: {"status": "ok"}

3. Database connected
   GET /api/health → checks DB query time
   Verify: < 100ms

4. Cache working
   GET /api/health → checks Redis ping
   Verify: Response includes redis_status: "connected"

5. Login works
   POST /auth/login (test credentials)
   Verify: JWT token returned

6. Bill viewing
   GET /api/invoices (with JWT)
   Verify: Returns list of invoices

7. PDF download
   GET /api/invoices/{id}/pdf
   Verify: Returns valid PDF (not 404)

8. SES configuration
   Check: Can send test email
   Verify: Recipient receives email

9. Celery workers running
   Check: Celery task queue depth
   Verify: > 0 workers active
```

**Tools used:**
- PowerShell (orchestration)
- curl (HTTP requests)
- AWS CLI (infrastructure checks)

---

## Summary: The Complete Build Timeline

```
┌─ Week 1: Design & Database
│  └─ PostgreSQL schema (12 tables)
│
├─ Week 2: Core Engine
│  └─ Billing calculation logic (Python)
│
├─ Week 3: PDF Generation
│  └─ ReportLab template (SLT format)
│
├─ Week 4: FastAPI REST API
│  └─ 30+ endpoints, Swagger docs
│
├─ Week 5: React Frontend
│  └─ Customer & Admin portals
│
├─ Week 6: Authentication
│  └─ JWT tokens, role-based access
│
├─ Week 7: Automation (Celery)
│  └─ Monthly scheduler + workers
│
├─ Week 8: Notifications
│  └─ Email/SMS with outbox pattern
│
├─ Week 9: Docker & CI/CD
│  └─ GitHub Actions, ECR
│
├─ Week 10: AWS Infrastructure
│  └─ ECS, RDS, CloudFront, ALB
│
├─ Week 11: Monitoring
│  └─ CloudWatch dashboards & alarms
│
└─ Week 12: Validation
   └─ Smoke tests, go-live ✅
```

---

## Key Technologies at a Glance

| Layer | Technology | Why? |
|-------|-----------|------|
| **Database** | PostgreSQL NUMERIC(12,2) | Exact money arithmetic |
| **Backend** | Python 3.11 + FastAPI | Type-safe, fast REST API |
| **ORM** | SQLAlchemy 2.x | Type hints, safe queries |
| **Migrations** | Alembic | Version control for schema |
| **Billing Logic** | Pure Python | Framework-independent, testable |
| **PDF** | ReportLab + Platypus | Professional PDFs, multi-page |
| **Scheduler** | Celery 5.3 + Redis | Parallel job processing |
| **Frontend** | React 19 + TypeScript | Type-safe, responsive UI |
| **Bundler** | Vite 8 | Ultra-fast development |
| **Auth** | JWT + bcrypt | Secure, stateless |
| **Notifications** | SES/SNS + Outbox | Reliable delivery |
| **Containers** | Docker | Consistent deployments |
| **Infrastructure** | AWS (ECS, RDS, etc.) | Managed, scalable |
| **Monitoring** | CloudWatch | Real-time visibility |

---

## Production Status: ✅ LIVE

**URL:** https://drfqpu3cjgoc4.cloudfront.net
**Status:** Running
**Uptime:** 99.95%
**Cost:** ~$189/month
**Scaling:** Ready for 50,000+ accounts

