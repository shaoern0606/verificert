# Integration Scenario: Issue -> Blockchain -> Verify -> Revoke -> Verify Again

1. Start PostgreSQL and Hardhat.
2. Deploy `VerifiCertRegistry` with `npm run deploy:local`.
3. Seed demo data with `cd apps/api; python -m app.db.seed`.
4. Login as `issuer@abc-academy.local`.
5. POST `/api/certificates` with a PDF file.
6. GET `/api/verify/{certificate_id}` and expect `VERIFIED`.
7. POST `/api/verify/upload` with modified bytes and expect `INVALID`.
8. POST `/api/certificates/{certificate_id}/revoke`.
9. GET `/api/verify/{certificate_id}` and expect `REVOKED`.
