# VERIFICERT

**Blockchain-Based Verifiable Digital Credential Platform with AI Fraud Detection**

VERIFICERT is a verifiable digital credential platform that allows approved organizations to issue digital certificates, recipients to manage their credentials, and anyone to verify whether a certificate is authentic, unchanged, active, expired, or revoked.

---

## ✨ Features

- 🔐 JWT authentication (httpOnly cookies) with role-based access control
- 🏢 Organization and issuer management, with self-service issuer applications reviewed by an admin
- 📜 Digital certificate issuance with an embedded, scannable QR code
- 🔗 Blockchain-based certificate registration
- 🔍 Public certificate verification — by ID, by dragging in a file, or by scanning a QR code
- 📄 SHA-256 document hash verification for PDF and image certificates
- 🚫 Certificate revocation
- 🤖 AI-assisted fraud/risk analysis using Gemini multimodal document review (optional)
- 📊 Admin and issuer dashboards
- 📝 Audit logging
- 🗄️ PostgreSQL database
- ⛓️ Local Hardhat blockchain
- 🌐 Sepolia-ready smart contract deployment
- 🚦 Rate limiting on auth and verification endpoints
- 🐳 Dockerized `api`/`web` with CI (lint, test, build)
- 🔎 Search and status filtering on certificate, issuer, and audit-log listings
- 🌐 Public issuer directory
- 📇 Shareable, embeddable credential badges (SVG) with LinkedIn/copy-link sharing
- 🔑 Admin-issued API keys for programmatic verification, with per-key audit attribution
- 📤 Bulk certificate issuance from a CSV (auto-generates each certificate PDF)
- 📧 Email notifications on issue/revoke and certificate-expiry reminders (optional, via Resend)

---

## 🏗️ Architecture

VERIFICERT is structured as a monorepo:

```text
verificert/
├── apps/
│   ├── web/                 # Next.js frontend
│   └── api/                 # FastAPI backend
│
├── contracts/               # Solidity smart contracts
│   ├── contracts/
│   └── scripts/
│
├── packages/
│   └── shared/              # Shared models and verification states
│
├── infrastructure/
│   └── docker-compose.yml   # PostgreSQL, api, web (Hardhat stays host-run)
│
├── .github/workflows/       # CI: lint + test + build (contracts, api, web) + docker build
│
├── docs/
│
├── .env.example
└── package.json
```

---

## Technology Stack

| Layer | Technology |
| ----- | ---------- |
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | FastAPI, Pydantic, SQLAlchemy |
| Database | PostgreSQL |
| Blockchain | Solidity, Hardhat, OpenZeppelin |
| AI | LangGraph, LangChain Core, Google Gemini (multimodal document review) |
| Authentication | JWT in httpOnly cookies, rate-limited via slowapi |
| Document Integrity | SHA-256, QR-stamped PDFs (pypdf + reportlab + qrcode) |
| Infrastructure | Docker Compose, GitHub Actions CI |

---

## ⛓️ Why Blockchain?

Blockchain is used as an immutable verification layer rather than a document storage system.

The actual certificate files remain off-chain.

VERIFICERT calculates a SHA-256 hash of the exact certificate PDF or image and registers the hash together with important certificate metadata on-chain.

```text
Certificate PDF or image
      │
      ▼
   SHA-256
      │
      ▼
Document Hash
      │
      ▼
Blockchain Registry
```

This allows a verifier to determine whether a certificate has been modified after issuance.

---

## 🔍 Verification Logic

Verification follows a strict hierarchy:

1. Certificate exists
2. Issuer is recognized and approved
3. Blockchain record exists
4. Uploaded document hash matches the registered hash
5. Certificate has not been revoked
6. Certificate has not expired
7. Metadata is consistent (checked via a Gemini multimodal document review when `GOOGLE_API_KEY` is configured; skipped with an honest "not configured" note otherwise)
8. AI fraud analysis provides additional risk context

AI cannot override cryptographic or blockchain verification failures. If the certificate's own database record marks it revoked but the live blockchain lookup can't currently reach a record (e.g. a local dev chain was reset), the database's last known status wins rather than silently reporting "not revoked."

For example:

```text
Hash mismatch
     ↓
INVALID

Revoked certificate
     ↓
REVOKED

Expired certificate
     ↓
EXPIRED

All checks passed
     ↓
VERIFIED
```

---

## 🚀 Quickstart & Setup

### Prerequisites

- **Node.js 20+** & **npm 10+**
- **Python 3.12+**
- **Docker Desktop** (running)

---

### 1. Clone & Configure

```bash
git clone <YOUR_REPOSITORY_URL>
cd verificert
cp .env.example .env
npm install
```

---

### 2. Run the Stack (4 Terminals)

**Terminal 1 — Database & Blockchain**
```bash
# Start PostgreSQL
docker compose -f infrastructure/docker-compose.yml up -d

# Start Hardhat local node
npm run blockchain
```

**Terminal 2 — Smart Contract Deployment**
```bash
# Deploy locally; copy the printed contract and wallet addresses into .env.
npm run deploy:local
```

**Terminal 3 — FastAPI Backend**
```bash
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Seed users, organizations, issuers, recipients, and the local demo certificate.
# Run after the local contract deployment so blockchain-backed seed data is created.
cd ../..
npm run seed
cd apps/api
python -m uvicorn app.main:app --reload --port 8000
```

> **macOS Note:** If Passlib causes bcrypt errors, run `pip install bcrypt==4.0.1`.

**Terminal 4 — Next.js Frontend**
```bash
npm run web
```

---

### Alternative: Dockerized `api` + `web`

Once the Hardhat node is running and the contract is deployed (Terminals 1–2 above still apply — Hardhat stays host-run since local dev restarts its in-memory chain often), Postgres/api/web can run in containers instead of Terminals 3–4:

```bash
docker compose -f infrastructure/docker-compose.yml up -d --build
```

The `api` container reaches your host's Hardhat node via `host.docker.internal:8545`. Run `npm run seed` from the host once the API container is healthy.

---

### 3. Service Access Points

| Service | URL | Notes |
| --- | --- | --- |
| **Frontend** | `http://localhost:3000` | Verification UI & Dashboards |
| **Backend API** | `http://localhost:8000` | FastAPI instance |
| **API Docs** | `http://localhost:8000/docs` | Interactive Swagger documentation |
| **Local Node** | `http://127.0.0.1:8545` | Hardhat RPC endpoint |
| **PostgreSQL** | `localhost:5432` | Containerized relational database |

---

## 👤 Bootstrap Accounts

These local development accounts are created by `npm run seed` and can be used to sign in immediately:

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@verificert.local` | `Password123!` |
| Issuer | `issuer@abc-academy.local` | `Password123!` |
| Recipient | `john.tan@example.com` | `Password123!` |

All seven seeded issuer profiles have login accounts with password `Password123!`:

```text
issuer@abc-academy.local
registrar@northbridge.example
certificates@cloudskills-academy.local
admin@brightpath-institute.local
verification@techbridge-academy.local
pending@abc-academy.local
suspended@northbridge.example
```

Pending and suspended issuers can sign in, but they cannot issue certificates until an admin reviews and approves them from the Admin Issuer Management page.

Use these bootstrap accounts only for initial local setup. Change passwords and rotate credentials before any real deployment.

---

## ⛓️ Real Blockchain Requirement

VERIFICERT no longer supports fake certificate registration. Every issued certificate must be written to `VerifiCertRegistry` through Web3 before it is stored as active in the application database.

The backend requires:

```env
BLOCKCHAIN_RPC_URL=http://127.0.0.1:8545
BLOCKCHAIN_PRIVATE_KEY=
BLOCKCHAIN_ADMIN_PRIVATE_KEY=
VERIFICERT_CONTRACT_ADDRESS=
ABC_ACADEMY_PRIVATE_KEY=
NORTHBRIDGE_PRIVATE_KEY=
CLOUDSKILLS_PRIVATE_KEY=
BRIGHTPATH_PRIVATE_KEY=
TECHBRIDGE_PRIVATE_KEY=
ABC_ACADEMY_WALLET_ADDRESS=
NORTHBRIDGE_WALLET_ADDRESS=
CLOUDSKILLS_WALLET_ADDRESS=
BRIGHTPATH_WALLET_ADDRESS=
TECHBRIDGE_WALLET_ADDRESS=
BLOCKCHAIN_NETWORK_NAME=hardhat-local
REQUIRE_BLOCKCHAIN=true
```

For multi-issuer local development, each approved issuer uses its own Hardhat key and matching wallet address. `npm run deploy:local` registers the five approved issuer wallets on the new local contract and prints their `*_WALLET_ADDRESS` values. The API selects the signer from the authenticated issuer's database wallet and rejects missing or mismatched keys.

For issuance, the private key must belong to the same wallet address configured on the issuer record, and that wallet must be approved in the smart contract. Verification reads the contract live and compares:

- certificate ID exists on-chain
- on-chain document hash matches the uploaded or stored file hash
- on-chain issuer address matches the approved issuer wallet
- on-chain revocation and expiry state

If the blockchain record is missing or unreachable, the certificate is not treated as commercially verified.

---

## 🤖 AI Document Review (optional)

Verification runs a real Gemini multimodal call that reads the certificate file and cross-checks the extracted recipient/course/issuer fields against the database record, feeding genuine `metadata_match`/discrepancy signals into the risk score (this replaced a previous placeholder that only produced a deterministic score with no actual document inspection).

```env
GOOGLE_API_KEY=
GOOGLE_AI_MODEL=gemini-2.5-flash   # optional, defaults shown
```

Without a key, verification still works fully (blockchain/hash/revocation checks are unaffected) — the AI section just reports `"AI document review is not configured (missing GOOGLE_API_KEY)."` instead of silently pretending to have checked anything. Results are cached per certificate document hash so a page refresh doesn't re-bill the API.

---

## 📧 Email Notifications (optional)

Recipients get emailed when a certificate is issued or revoked, via [Resend](https://resend.com):

```env
RESEND_API_KEY=
EMAIL_FROM=VerifiCert <onboarding@resend.dev>   # optional, default shown
CERTIFICATE_EXPIRY_REMINDER_DAYS=30              # optional, default shown
```

Without a key, sends are skipped with a log line — nothing blocks issuance/revocation on email delivery. **With** a key but no verified sending domain, Resend's sandbox address (`onboarding@resend.dev`) can only deliver to the account owner's own verified email — sends to any other address fail (logged, not thrown). Verify a domain in Resend and point `EMAIL_FROM` at it to send to real recipients.

Expiry reminders aren't on a scheduler — there's no task-queue/cron infrastructure in this project yet. Run it manually or put it on a cron entry:

```bash
cd apps/api && .venv/bin/python -m app.jobs.expiry_reminders
```

It emails each `ACTIVE` certificate expiring within the reminder window exactly once (tracked via `expiry_reminder_sent_at`), then exits.

---

## 📡 API Endpoints

The backend provides APIs for:

**Authentication**
```text
POST  /api/auth/register              # role is always RECIPIENT; client-supplied roles are ignored
POST  /api/auth/login
POST  /api/auth/logout                # clears the session cookie
GET   /api/auth/me
PATCH /api/auth/users/{user_id}/role  # admin only
```

Sessions are httpOnly, `Secure`, `SameSite=None` cookies (30-minute expiry, no refresh token — see Known Limitations).

**Issuers**
```text
POST /api/issuers                     # any authenticated user; creates a PENDING profile tied to their own account
GET  /api/issuers                     # admin only, paginated, ?q= and ?status= filters
GET  /api/issuers/directory           # public; approved issuers only, ?q= filter
GET  /api/issuers/{issuer_id}
GET  /api/issuers/me                  # full profile: contact, wallet, description, website
POST /api/issuers/{issuer_id}/approve # also promotes the linked account's role to ISSUER
POST /api/issuers/{issuer_id}/suspend
```

**Certificates**
```text
POST /api/certificates                       # issues, stamps a QR into the PDF, and registers on-chain atomically
POST /api/certificates/bulk                  # CSV of recipients -> one certificate per row, partial-success report
GET  /api/certificates                       # paginated, ?q= and ?status= filters
GET  /api/certificates/{certificate_id}
POST /api/certificates/{certificate_id}/revoke
GET  /api/certificates/{certificate_id}/download    # streams the actual stored file
GET  /api/certificates/{certificate_id}/badge.svg   # public, embeddable status badge (cheap DB read, not a full re-verify)
```

Issuing (single or bulk) checks that the calling issuer actually owns the `issuer_id` they're submitting for — an issuer can't issue against another organization's profile even if it's approved.

**Verification**
```text
GET  /api/verify/{certificate_id}
POST /api/verify
POST /api/verify/upload   # certificate_id is optional — omit it to identify the certificate purely
                           # from the uploaded file's SHA-256 hash (drag-and-drop / no-ID verification)
```

Verify endpoints accept an optional `X-API-Key` header (see API Keys below) — when present and valid, audit-log entries are attributed to the key's label instead of `"public"`.

**API Keys** (admin only)
```text
POST   /api/admin/api-keys           # returns the plaintext key once — it is never shown again
GET    /api/admin/api-keys
DELETE /api/admin/api-keys/{key_id}
```

**AI**
```text
POST /api/ai/analyze-certificate
```

**Dashboards**
```text
GET /api/dashboard/admin   # includes both certificates_by_status and verification_outcomes chart data
GET /api/dashboard/issuer
```

**Audit**
```text
GET /api/audit-logs   # paginated, ?q= and ?action= filters
```

---

## 🧪 Testing

**Smart Contracts**
```bash
npm --workspace contracts test
```

**Backend**
```bash
cd apps/api && source .venv/bin/activate
python -m pytest
```

**Linting**
```bash
npm run lint
```

CI (`.github/workflows/ci.yml`) runs all three test suites plus a Docker build on every push/PR.

---

## 🔐 Security

Never commit `.env`, private keys, API keys, wallet secrets, or production credentials. Use environment variables or a dedicated secret manager for production.

Hardhat development accounts are publicly known and must **never** be used on Mainnet or any real network.

Fixed in this project's security pass (previously a client could self-register as `ADMIN` and forge issuer profiles under any email):
- `POST /api/auth/register` ignores any client-supplied role — every new account is `RECIPIENT`. Becoming an `ISSUER` requires applying (`POST /api/issuers`, tied to your own authenticated account) and an admin approving it; becoming a second `ADMIN` requires an existing admin to call `PATCH /api/auth/users/{id}/role`.
- `POST /api/issuers` requires authentication and binds the new issuer profile to the caller's own email — it can no longer be created for an arbitrary email with no account behind it.
- Session tokens live in httpOnly, `Secure`, `SameSite=None` cookies instead of `localStorage`, so they aren't readable by JS/XSS. `POST /api/auth/logout` actually invalidates the session cookie.
- Login, register, and verify endpoints are rate-limited (`slowapi`) against brute force and scraping.
- CORS origins are driven by the `CORS_ORIGINS` setting instead of being hardcoded, so a production origin allowlist can be configured without code changes.
- Issuing a certificate (single or bulk) now checks the calling issuer actually owns the `issuer_id` submitted — previously any `ISSUER`-role account could issue against a *different, unrelated* approved issuer's profile as long as they knew its ID.
- API keys are stored as SHA-256 hashes (never the plaintext), shown to the admin exactly once at creation, and can be revoked individually without touching any user account.

---

## 🌍 Sepolia Deployment

For Sepolia deployment, configure `.env`:
```env
SEPOLIA_RPC_URL=https://...
BLOCKCHAIN_PRIVATE_KEY=0x...
```

Then deploy:
```bash
npm run deploy:sepolia
```

---

## 🏭 Production Considerations

For production deployment:
- Replace local file storage with S3/IPFS.
- Use managed PostgreSQL with backups.
- Move `BLOCKCHAIN_PRIVATE_KEY` into a secure signer, HSM, MPC wallet, or cloud KMS-backed signing service — or better, a relayer pattern so issuers never custody gas-paying keys.
- Add refresh tokens and device/session revocation (current sessions are a single short-lived cookie with no refresh — see Known Limitations).
- Implement organization-scoped authorization policies.
- Move AI analysis to asynchronous workers if verification volume grows (it currently runs Gemini synchronously inline, mitigated by per-document-hash caching and rate limiting).
- Add monitoring, centralized logging, and alerting.
- Add email verification and password reset. Email notifications on issue/revoke are already wired (see AI/Email sections above) but need a verified Resend sending domain to reach real recipients.
- Swap the rate limiter's in-memory store for Redis if running more than one API instance.
- Move the SQLAlchemy session model to async if verification traffic outgrows a single sync connection pool.

---

## ✅ Implemented

- JWT authentication (httpOnly cookies) & role-based authorization, with self-service issuer applications and admin approval/promotion
- Organization management & issuer approval/suspension
- Certificate creation, issuance, SHA-256 document hashing, and QR-code stamping directly into the issued PDF
- Blockchain registration and verification logic, with a database fallback when the live chain record is unreachable
- Certificate revocation & real file download (streams the actual stored document)
- Public verification UI: by certificate ID, by dragging in a file (matched purely by document hash, no ID required), or by scanning a QR code with the camera
- Real Gemini-based AI document review (optional, degrades honestly without a key), cached per document hash
- Admin and Issuer dashboards, with pagination on certificate/issuer/audit-log listings
- Rate limiting on auth and verification endpoints
- Solidity registry with OpenZeppelin AccessControl
- Duplicate certificate prevention
- PostgreSQL persistence
- Bootstrap seed data without fake certificate transactions
- Dockerfiles for `api`/`web` and CI (lint, test, build) via GitHub Actions
- Search and status filtering on certificate, issuer, and audit-log lists
- Public issuer directory, shareable/embeddable credential badges, and admin-issued API keys with per-key audit attribution
- Bulk CSV certificate issuance (each row gets its own generated, QR-stamped, blockchain-registered PDF) with partial-success reporting
- Email notifications on issue/revoke and a runnable (not scheduled) certificate-expiry reminder job, via Resend

---

## ⚠️ Known Limitations

**Blockchain / data consistency**
- The local Hardhat node is in-memory and ephemeral — restarting it wipes all on-chain history while PostgreSQL keeps its records. This causes real, visible inconsistency (a certificate the DB says is `REVOKED` but the chain has no record for at all) until a certificate is reissued/re-registered against the new chain. Verification now falls back to the DB's last known revoked status when the chain record is missing, but the underlying desync (and needing to re-run `npm run deploy:local` + update `VERIFICERT_CONTRACT_ADDRESS` after every Hardhat restart) is a genuine local-dev limitation, not something fixed at the code level.
- Per-issuer private keys live in plaintext `.env` for 5 hardcoded demo organizations. This doesn't scale past the demo and isn't how real organizations' signing keys should be custodied (needs KMS/HSM/MPC or a relayer pattern — see Production Considerations).

**Auth**
- Sessions are a single httpOnly cookie with a 30-minute expiry and **no refresh token** — there's no way to extend a session without logging in again, and no server-side revocation list, so a stolen (pre-expiry) cookie is valid until it expires naturally. A logged-out user's *old* token (if captured earlier) isn't invalidated by logout, only the browser's cookie is cleared.
- No email verification or password reset flow — anyone can register with any email string without proving they own it.
- No CAPTCHA; rate limiting alone guards against automated brute force.
- Rate limiting is in-memory and per-process — it resets on restart and won't coordinate across multiple API instances behind a load balancer.

**AI review**
- The Gemini document review needs a valid `GOOGLE_API_KEY` and incurs a real API call (cost + latency) per uncached document; it's a synchronous inline call, not queued to a background worker.
- The AI is advisory only — it cannot override cryptographic/blockchain verification results, and it can be wrong (LLM extraction/comparison is not guaranteed accurate).

**Storage & scale**
- Certificate files live on local disk (`storage_path`), not S3/IPFS — they're lost if the container/volume is wiped, and there's no CDN or backup story.
- Pagination and basic search/status filtering exist on list endpoints, but there's no full-text ranking, saved filters, or advanced querying.
- No monitoring/alerting beyond request-logging middleware and application logs.

**Email**
- No email verification or password reset — email notifications piggyback on whatever address a user typed at registration/certificate creation, unverified.
- Expiry reminders require someone (or an external cron) to actually run `python -m app.jobs.expiry_reminders` — there's no in-app scheduler.
- Without a verified sending domain, Resend's sandbox sender can only deliver to the account owner's own address; real recipients need a verified domain configured via `EMAIL_FROM`.

**API keys**
- Keys are a flat admin-managed list with no scoping (every key can call every verify endpoint) and no expiry — revocation is manual and immediate, but there's no automatic key rotation or per-key rate-limit tier.

**Deferred by design (not attempted this pass)**
- **Multi-user issuer organizations** — an issuer profile is still one email = one login; there's no membership model for multiple staff under one organization. Deliberately deferred since it reshapes the core auth/ownership model.
- **Self-sovereign recipient wallets** — recipients are still identified by email, not an on-chain identity they control. Deliberately deferred as a product-direction decision, not a bundled feature.

**Frontend / testing**
- QR camera scanning (`getUserMedia` + `jsqr`) was implemented and unit/build-verified but not visually tested in a real browser in this environment (no camera/browser-automation tool was available) — worth a manual check, particularly camera permission prompts across browsers.
- Minimal automated test coverage (a handful of backend unit tests, contract tests; no frontend tests, and none of the newer routes — bulk issuance, API keys, badges, directory — have automated coverage yet).
- `sharp` and `postcss` show up as transitively vulnerable in `npm audit` for the web app; neither is actually used at runtime here (no `next/image` usage, `sharp` isn't even installed) — clearing them fully requires an untested Next.js 16 major upgrade, which wasn't done. The Next.js package itself was bumped from 15.1.5 → 15.5.23, which resolves the framework's own direct CVEs (the previous version had ~30 known advisories, including a critical one).
- The `contracts` workspace (Hardhat toolchain) has its own pre-existing `npm audit` findings in dev-only dependencies (e.g. `ws`); these are build/test tooling, not shipped to production, and weren't touched here.

---

## 📁 Operational Flow

The normal commercial issuance and verification flow is:

```text
1. Admin logs in
      ↓
2. Approves an issuer
      ↓
3. Issuer creates a certificate
      ↓
4. Certificate PDF or image is hashed
      ↓
5. Certificate hash is registered on blockchain
      ↓
6. Recipient receives the credential
      ↓
7. Public verifier uploads/scans the certificate
      ↓
8. SHA-256 hash is compared
      ↓
9. Blockchain record is checked
      ↓
10. Revocation + expiry status is checked
      ↓
11. AI performs fraud/risk analysis
      ↓
12. VERIFIABLE / INVALID result is displayed
```

---

## 🏆 Hackathon Value Proposition

VERIFICERT combines three layers of trust:

```text
                  VERIFICERT
                      │
     ┌────────────────┼────────────────┐
     ▼                ▼                ▼
CRYPTOGRAPHY      BLOCKCHAIN           AI
     │                │                │
  SHA-256         Immutable        Fraud/Risk
 Integrity         Registry         Analysis
     │                │                │
     └────────────────┼────────────────┘
                      ▼
             Trusted Verification
```

**Blockchain provides immutable proof of issuance.**

**SHA-256 provides proof that the document has not been altered.**

**AI provides additional fraud and risk intelligence.**

Together, these layers create a practical verification system for digital credentials.
