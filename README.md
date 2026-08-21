# VERIFICERT

Blockchain-Based Verifiable Digital Credential Platform with AI Fraud Detection.

VERIFICERT lets approved organizations issue digital certificates, recipients manage credentials, and public verifiers confirm whether a certificate was genuinely issued, unchanged, active, expired, or revoked.

## Architecture

The platform is a monorepo:

- `apps/web`: Next.js, React, TypeScript, Tailwind UI.
- `apps/api`: FastAPI, Pydantic, SQLAlchemy, Alembic, demo LangGraph AI workflow.
- `contracts`: Solidity `VerifiCertRegistry`, Hardhat local chain and Sepolia-ready config.
- `packages/shared`: shared verification states and models.
- `infrastructure`: PostgreSQL Docker Compose.
- `docs`: architecture diagrams and production notes.

Documents stay off-chain. The API hashes the exact PDF bytes with SHA-256, stores metadata and file references in PostgreSQL/local storage, and registers only certificate ID, document hash, issuer, timestamp, expiry, revocation status, and metadata URI on-chain.

## Why Blockchain

The blockchain is an immutable verification layer. It is not a document store. This makes independent verification possible without exposing sensitive certificate files publicly.

## Verification Rules

Final status is determined in this order:

1. Certificate exists.
2. Issuer is recognized and approved.
3. Blockchain record is present.
4. Uploaded document hash matches registered hash.
5. Certificate is not revoked.
6. Certificate is not expired.
7. Metadata is consistent.
8. AI fraud analysis provides risk context.

AI cannot override a hash mismatch, missing blockchain record, or revocation.

## Demo Accounts

- Admin: `admin@verificert.local` / `Password123!`
- Issuer: `issuer@abc-academy.local` / `Password123!`
- Recipient: `john.tan@example.com` / `Password123!`

## Windows 11 Setup

Install Node.js 20+, Python 3.12+, and Docker Desktop.

```powershell
Copy-Item .env.example .env
npm install
# pnpm is also supported:
# pnpm install
```

Start PostgreSQL:

```powershell
docker compose -f infrastructure/docker-compose.yml up -d
```

Start local blockchain:

```powershell
npm run blockchain
```

In a second terminal, deploy the registry:

```powershell
npm run deploy:local
```

Copy the printed `VERIFICERT_CONTRACT_ADDRESS` into `.env`.

Start the backend:

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m app.db.seed
python -m uvicorn app.main:app --reload --port 8000
```

Start the frontend:

```powershell
cd apps/web
npm run dev
```

Open:

- Web app: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- Demo verification: `http://localhost:3000/verify/CERT-2026-000001`

## Demo Mode

If `OPENAI_API_KEY`, `SEPOLIA_RPC_URL`, or `BLOCKCHAIN_PRIVATE_KEY` are missing, the app still runs in demo mode:

- Local Hardhat is used for contract development.
- Backend blockchain receipts are deterministic when no contract address is configured.
- AI fraud detection uses deterministic structured output through the LangGraph-compatible workflow.

## Testing

```powershell
npm --workspace contracts test
cd apps/api
python -m pytest
```

The included integration scenario is documented at `tests/integration/issue_verify_revoke.md`.

## Sepolia Deployment

Set:

```powershell
$env:SEPOLIA_RPC_URL="https://..."
$env:BLOCKCHAIN_PRIVATE_KEY="0x..."
npm --workspace contracts run deploy:local -- --network sepolia
```

Never commit private keys. Use environment variables or a secret manager.

## Production Considerations

- Replace local file storage with S3/IPFS through the storage service boundary.
- Use a managed PostgreSQL instance with backups.
- Use real OCR provider integration behind the OCR abstraction.
- Wire `BlockchainService` to `ethers.py` or a signing worker for production transactions.
- Add refresh tokens, device sessions, and organization-scoped authorization policies.
- Move AI analysis to an async worker for high-volume verification traffic.

## Implemented

- Normalized database schema for users, organizations, issuers, recipients, certificates, files, transactions, verification attempts, audit logs, wallets, and AI results.
- JWT auth and role guards.
- Certificate issue, hash, register, verify, revoke, audit, and dashboard APIs.
- Public verification UI with decisive result hierarchy and technical details.
- Solidity registry with events, access control, duplicate prevention, issuer suspension, and revocation.
- Demo seed data with 3 organizations, 5 issuers, 10 recipients, and 30 certificates.
- Deterministic AI risk assessment using Pydantic structured output.

## Known Limitations

- QR embedding into PDFs is represented by generated verification payloads; production PDF stamping should be added through a document rendering pipeline.
- OCR is abstracted in the architecture and AI flow, but demo extraction is deterministic.
- Real blockchain transaction submission from FastAPI is represented by the `BlockchainService` boundary and deterministic demo receipts until production signing is configured.
