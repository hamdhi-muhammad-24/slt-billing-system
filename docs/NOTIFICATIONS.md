# NOTIFICATIONS.md — Phase 5 Spec

Email (mandatory) and SMS (this phase) the customer **after a bill is generated**.
WhatsApp is optional/out for now. AWS SES wiring lives in Phase 6.

This is a **new layer**. It *reads* invoices and *calls* frozen code. It never edits the
engine, repository, PDF, API, auth, batch service, or scheduler.

---

## 1. Hard rules

1. **Frozen boundary.** The notifier only **reads** the `invoices` table and **writes** its
   own `notification_outbox` table. No billing/scheduler files are modified.
2. **Idempotent.** A given invoice is emailed once and texted once — ever. Re-running the
   scanner never double-sends. Enforced by a DB unique constraint, not by hope.
3. **Provider-agnostic.** Email and SMS each go through a small sender *interface*. Backends
   (MailHog/SMTP now, SES later; Twilio now, SNS later) are swapped by config.
4. **No PII in logs.** Log invoice id + status, never the email body, phone number, or address.
   All seed data stays synthetic.
5. **Money is never recomputed.** The email/SMS shows the invoice's **stored** `total_payable`
   string (e.g. `"4628.52"`), formatted for display — the notifier does zero arithmetic.

---

## 2. How it works (the outbox pattern)

Because billing is frozen, the notifier can't have billing "push" it work. Instead the
notifier **pulls**: it scans for invoices it hasn't handled yet, records them, and sends.

```
invoices (frozen, read-only)
        │
        ▼
  [ scan & enqueue ]  ← find invoices with no outbox row → insert QUEUED rows
        │
        ▼
 notification_outbox  ← the notifier's OWN table (statuses below)
        │
        ▼
   [ send pending ]   ← for each QUEUED row: render message → send via backend → mark SENT/FAILED
        │
        ├── EmailSender → SMTP/MailHog (now)   |  SES (Phase 6)
        └── SmsSender   → Twilio (now)         |  SNS (later, optional)
```

One operation, **`scan-and-send`**, does both halves: enqueue new invoices, then send queued
rows. Running it twice is safe (idempotent). It runs as a CLI command (dev) and as a Celery
task (scheduled by Beat in prod).

---

## 3. Data model — `notification_outbox`

One row **per invoice per channel** (so email and SMS are tracked independently).

| Column          | Type            | Notes |
|-----------------|-----------------|-------|
| `id`            | PK              | |
| `invoice_id`    | FK → invoices   | the bill being notified |
| `channel`       | enum            | `EMAIL` \| `SMS` |
| `status`        | enum            | `QUEUED` → `SENT` \| `FAILED` |
| `recipient`     | text            | email address or phone, resolved at enqueue time |
| `attempts`      | int default 0   | incremented per send try |
| `last_error`    | text null       | short error string on failure |
| `provider_ref`  | text null       | provider message id (e.g. Twilio SID) for traceability |
| `created_at`    | timestamptz     | |
| `sent_at`       | timestamptz null| |

**Unique constraint:** `(invoice_id, channel)` — the spine of idempotency. You physically
cannot insert a second EMAIL row for the same invoice.

New Alembic migration adds this one table + two enums. No existing table is touched.

---

## 4. Channels & backends

### Email — `app/notifications/senders/email.py`
- `EmailSender` interface: `send(to, subject, html, attachments) -> provider_ref`.
- `SmtpEmailSender` — talks to MailHog locally (host/port from env). Used now.
- `SesEmailSender` — **stub/placeholder** wired in Phase 6.
- Backend chosen by `EMAIL_BACKEND` env var (`smtp` | `ses`).

### SMS — `app/notifications/senders/sms.py`
- `SmsSender` interface: `send(to, body) -> provider_ref`.
- `TwilioSmsSender` — uses the official `twilio` Python package. Dev uses **Twilio test
  credentials** (magic numbers that validate the call without sending a real text / charging).
- Backend chosen by `SMS_BACKEND` env var (`twilio` | `console`).
- `console` backend just prints — handy when you don't want to hit Twilio at all.

Both interfaces are tiny, so they're trivially unit-tested with a **fake backend** that records
calls instead of sending.

---

## 5. Recipient resolution

Email + phone come from the customer record linked to the invoice
(`invoices → … → customers.user_id → users`). **⚠ Verify against your real schema** — match
whatever columns actually hold email/phone (likely `users.email` and a `customers.phone` /
`mobile` column). Per project principle, if this spec disagrees with the frozen models, the
**spec is corrected to match the models**, never the reverse.

If a customer has no email, that EMAIL row goes `FAILED` with `last_error="no email on file"`
and the run continues. Same idea for missing phone.

---

## 6. Message content

- **Email:** subject like `Your SLT bill for <period> — Rs <total_payable>`. Short HTML body
  (greeting, account no, period, amount due, due date) **plus the PDF**. Default: attach the
  PDF read from its stored path. Option (`EMAIL_USE_SIGNED_LINK=true`): instead embed the
  short-lived signed PDF link built in Phase 3.
- **SMS:** one short line, e.g. `SLT: bill for <period> is Rs <total_payable>. View: <link>`.
  No attachment. Keep under 160 chars.
- Templates live in `app/notifications/templates/`. Amounts come straight from the invoice
  snapshot via `formatLKR`-style formatting — **no recomputation**.

---

## 7. Failure handling & retries

- Each send increments `attempts`. On exception → status `FAILED`, store short `last_error`.
- A failed row is retried on the next `scan-and-send`, up to `NOTIFY_MAX_ATTEMPTS` (e.g. 3).
- After max attempts it stays `FAILED` and is **skipped** (a "dead letter" you can inspect).
- One bad recipient never stops the batch — per-row try/except, mirroring the billing batch.

---

## 8. Triggering — without editing frozen code

- **Core:** `scan-and-send` lives in `app/notifications/service.py`.
- **Dev / manual:** `python -m app.notifications.cli send-pending`.
- **Scheduled:** a Celery task `notify_pending` in `app/notifications/tasks.py`, registered on
  the **existing** Celery app via `@celery_app.task`. We rely on Celery **autodiscovery** so
  `app/scheduler/celery_app.py` stays untouched. The Beat entry (run every N minutes, or right
  after the monthly billing job) is added from the notifications module using Celery's
  `on_after_configure` signal — again, no edit to the frozen scheduler file.
- Visible in **Flower** like your other tasks.

> If your frozen `celery_app.py` does **not** autodiscover `app.*` tasks, the single minimal
> wiring touch is adding `app.notifications.tasks` to its include list. We'll confirm which
> case you're in during the build and pick the no-edit path if available.

---

## 9. Config additions (`.env.example`)

```
# Email
EMAIL_BACKEND=smtp            # smtp | ses
SMTP_HOST=localhost
SMTP_PORT=1025                # MailHog
EMAIL_FROM="SLT Billing <billing@slt.lk>"
EMAIL_USE_SIGNED_LINK=false

# SMS
SMS_BACKEND=console           # console | twilio
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM=

# Notifier
NOTIFY_MAX_ATTEMPTS=3
```

---

## 10. Testing

- **Unit:** fake email/SMS backends record calls — assert subject/recipient/body, no network.
- **Idempotency:** enqueue same invoice twice → exactly one outbox row per channel; second
  `scan-and-send` sends nothing.
- **Retry:** force a backend error → row `FAILED`, `attempts` rises, retried next run, capped
  at `NOTIFY_MAX_ATTEMPTS`.
- **Integration (manual):** generate a bill → `scan-and-send` → see the email in MailHog UI
  (http://localhost:8025) with the PDF attached; SMS validated via Twilio test creds / console.

---

## 11. Out of scope (Phase 5)

- WhatsApp (optional, later).
- Real AWS SES / SNS wiring + deployment (**Phase 6**).
- Customer notification preferences / opt-out UI (could be a later enhancement).

---

## 12. Build plan (3 chunks — exact Claude Code prompts given per chunk)

**Chunk 1 — Foundation**
🎯 Config keys, `notification_outbox` model + migration, email + SMS sender interfaces with
   backends (SMTP, Twilio, console) and a fake backend for tests.
📂 `app/core/config.py` (add keys), `app/db/models.py`? **no** → put outbox model in
   `app/notifications/models.py`, new Alembic migration, `app/notifications/senders/`.
✅ `alembic upgrade head` creates the table; `pytest` green on sender unit tests.

**Chunk 2 — Service, templates, CLI**
🎯 `scan-and-send` (enqueue new invoices → send queued), recipient resolution, email/SMS
   templates, retries, and a `send-pending` CLI command.
📂 `app/notifications/service.py`, `app/notifications/templates/`, `app/notifications/cli.py`.
✅ Generate a bill → `python -m app.notifications.cli send-pending` → email appears in MailHog
   with PDF attached; re-running sends nothing (idempotent).

**Chunk 3 — Schedule + harden**
🎯 `notify_pending` Celery task (autodiscovered) + Beat entry via signal; idempotency/retry
   tests; confirm it shows in Flower.
📂 `app/notifications/tasks.py`, `tests/test_notifications.py`.
✅ Task runs on schedule, visible in Flower; full test suite green.

**Commit after each chunk.** Tag `phase-5-notifications` when all three pass.
