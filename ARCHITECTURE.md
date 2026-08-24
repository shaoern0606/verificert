# VERIFICERT Architecture

## System Architecture

```mermaid
flowchart LR
  Web[Next.js Web App] --> API[FastAPI API]
  API --> DB[(PostgreSQL)]
  API --> Storage[Local Certificate Storage]
  API --> AI[LangGraph Fraud Workflow]
  API --> Chain[BlockchainService]
  Chain --> Contract[VerifiCertRegistry]
  Contract --> Hardhat[Hardhat Local Chain]
  Contract -. Sepolia-ready .-> Sepolia[Sepolia Testnet]
  Public[Public Verifier] --> Web
  Recipient[Recipient] --> Web
  Issuer[Issuer] --> Web
  Admin[Admin] --> Web
```

## Certificate Issuance Sequence

```mermaid
sequenceDiagram
  actor Issuer
  participant Web
  participant API
  participant Storage
  participant DB
  participant Chain as BlockchainService
  participant Contract
  Issuer->>Web: Submit recipient metadata + PDF
  Web->>API: POST /api/certificates
  API->>API: Validate file type and size
  API->>API: SHA-256 exact PDF bytes
  API->>Storage: Store PDF off-chain
  API->>DB: Store metadata and file hash
  API->>Chain: issue_certificate
  Chain->>Contract: issueCertificate
  Contract-->>Chain: CertificateIssued event
  Chain-->>API: transaction receipt
  API->>DB: Store transaction, audit event
  API-->>Web: Certificate ID, hash, tx, QR URL
```

## Verification Sequence

```mermaid
sequenceDiagram
  actor Verifier
  participant Web
  participant API
  participant DB
  participant Chain
  participant AI
  Verifier->>Web: Open /verify/CERT-2026-000001
  Web->>API: GET /api/verify/{certificate_id}
  API->>DB: Load certificate, issuer, transaction
  API->>Chain: verify_certificate
  API->>API: Apply authoritative verification hierarchy
  API->>AI: Run optional risk analysis
  AI-->>API: Structured risk result
  API->>DB: Store verification attempt and audit log
  API-->>Web: Decisive status + details
```

## Upload Hash Check

```mermaid
flowchart TD
  PDF[Uploaded certificate PDF] --> Bytes[Read exact bytes]
  Bytes --> Hash[SHA-256 hash]
  Hash --> Compare{Matches registered hash?}
  Compare -- Yes --> Continue[Continue status checks]
  Compare -- No --> Invalid[INVALID / Document hash mismatch]
```

## LangGraph Workflow

```mermaid
flowchart TD
  START --> document_ingestion
  document_ingestion --> metadata_extraction
  metadata_extraction --> issuer_check
  issuer_check --> blockchain_check
  blockchain_check --> hash_check
  hash_check --> visual_consistency_check
  visual_consistency_check --> risk_assessment
  risk_assessment --> final_result
  final_result --> END
```

## Blockchain Interaction Flow

```mermaid
flowchart LR
  API[FastAPI Services] --> Boundary[BlockchainService]
  Boundary --> Issue[issue_certificate]
  Boundary --> Verify[verify_certificate]
  Boundary --> Revoke[revoke_certificate]
  Boundary --> Register[register_issuer]
  Boundary --> Suspend[suspend_issuer]
  Issue --> Contract[VerifiCertRegistry]
  Verify --> Contract
  Revoke --> Contract
  Register --> Contract
  Suspend --> Contract
```

## Database ER Diagram

```mermaid
erDiagram
  users {
    string id PK
    string email
    string role
  }
  organizations {
    string id PK
    string name
  }
  issuers {
    string id PK
    string organization_id FK
    string wallet_address
    string status
  }
  recipients {
    string id PK
    string email
  }
  certificate_files {
    string id PK
    string document_hash
    string storage_path
  }
  blockchain_transactions {
    string id PK
    string transaction_hash
    string network
  }
  certificates {
    string id PK
    string certificate_id
    string issuer_id FK
    string recipient_id FK
    string file_id FK
    string blockchain_transaction_id FK
    string status
  }
  verification_attempts {
    string id PK
    string certificate_id
    string outcome
  }
  audit_logs {
    string id PK
    string action
    string certificate_id
  }
  ai_analysis_results {
    string id PK
    string certificate_id
    int risk_score
  }
  issuer_wallets {
    string id PK
    string issuer_id FK
    string wallet_address
  }
  organizations ||--o{ issuers : owns
  issuers ||--o{ certificates : issues
  recipients ||--o{ certificates : receives
  certificate_files ||--|| certificates : backs
  blockchain_transactions ||--o{ certificates : records
  certificates ||--o{ verification_attempts : checked_by
  certificates ||--o{ audit_logs : referenced_by
  certificates ||--o{ ai_analysis_results : analyzed_by
  issuers ||--o{ issuer_wallets : controls
```
