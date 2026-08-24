# VERIFICERT

**Blockchain-Based Verifiable Digital Credential Platform with AI Fraud Detection**

VERIFICERT is a verifiable digital credential platform that allows approved organizations to issue digital certificates, recipients to manage their credentials, and anyone to verify whether a certificate is authentic, unchanged, active, expired, or revoked.

---

## ✨ Features

- 🔐 JWT authentication with role-based access control
- 🏢 Organization and issuer management
- 📜 Digital certificate issuance
- 🔗 Blockchain-based certificate registration
- 🔍 Public certificate verification
- 📄 SHA-256 document hash verification for PDF and image certificates
- 🚫 Certificate revocation
- 🤖 AI-assisted fraud/risk analysis
- 📊 Admin and issuer dashboards
- 📝 Audit logging
- 🗄️ PostgreSQL database
- ⛓️ Local Hardhat blockchain
- 🌐 Sepolia-ready smart contract deployment

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
│   └── docker-compose.yml   # PostgreSQL
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
| AI | LangGraph, LangChain Core, Pydantic |
| Authentication | JWT |
| Document Integrity | SHA-256 |
| Infrastructure | Docker Compose |

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
7. Metadata is consistent
8. AI fraud analysis provides additional risk context

AI cannot override cryptographic or blockchain verification failures.

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

## 📡 API Endpoints

The backend provides APIs for:

**Authentication**
```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

**Issuers**
```text
GET  /api/issuers
POST /api/issuers
GET  /api/issuers/{issuer_id}
GET  /api/issuers/me
POST /api/issuers/{issuer_id}/approve
POST /api/issuers/{issuer_id}/suspend
```

**Certificates**
```text
POST /api/certificates
GET  /api/certificates
GET  /api/certificates/{certificate_id}
POST /api/certificates/{certificate_id}/issue
POST /api/certificates/{certificate_id}/revoke
GET  /api/certificates/{certificate_id}/download
```

**Verification**
```text
GET  /api/verify/{certificate_id}
POST /api/verify
POST /api/verify/upload
```

**AI**
```text
POST /api/ai/analyze-certificate
```

**Dashboards**
```text
GET /api/dashboard/admin
GET /api/dashboard/issuer
```

**Audit**
```text
GET /api/audit-logs
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

---

## 🔐 Security

Never commit `.env`, private keys, API keys, wallet secrets, or production credentials. Use environment variables or a dedicated secret manager for production.

Hardhat development accounts are publicly known and must **never** be used on Mainnet or any real network.

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
- Integrate a real OCR provider.
- Move `BLOCKCHAIN_PRIVATE_KEY` into a secure signer, HSM, MPC wallet, or cloud KMS-backed signing service.
- Add refresh tokens and device sessions.
- Implement organization-scoped authorization policies.
- Move AI analysis to asynchronous workers.
- Add monitoring and centralized logging.
- Use secure wallet/key management.
- Upgrade dependencies to currently supported versions before production deployment.

---

## ✅ Implemented

- JWT authentication & role-based authorization
- Organization management & issuer approval/suspension
- Certificate creation, issuance, and SHA-256 document hashing
- Blockchain registration and verification logic
- Certificate revocation & download
- Public verification UI & audit logs
- Admin and Issuer dashboards
- Solidity registry with OpenZeppelin AccessControl
- Duplicate certificate prevention
- PostgreSQL persistence
- Structured AI risk assessment
- Bootstrap seed data without fake certificate transactions

---

## ⚠️ Known Limitations

- QR embedding into PDFs is represented by generated verification payloads; production PDF stamping should be added through a document rendering pipeline.
- OCR is abstracted through the architecture; production OCR integration is still required.
- Local blockchain transactions use Hardhat only for development. Commercial use should deploy the registry on a public or consortium network with monitored RPC access.
- Production blockchain signing should use a dedicated signing service or secure wallet infrastructure; do not keep issuer private keys in a plain `.env` file.
- AI analysis is advisory and cannot override cryptographic verification results.

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
```
