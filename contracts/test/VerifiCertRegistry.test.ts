import { expect } from "chai";
import { ethers } from "hardhat";

describe("VerifiCertRegistry", function () {
  async function fixture() {
    const [admin, issuer, other] = await ethers.getSigners();
    const Registry = await ethers.getContractFactory("VerifiCertRegistry");
    const registry = await Registry.deploy(admin.address);
    await registry.waitForDeployment();
    await registry.registerIssuer(issuer.address);
    return { registry, admin, issuer, other };
  }

  it("allows approved issuers to issue and verify certificates", async function () {
    const { registry, issuer } = await fixture();
    const hash = ethers.keccak256(ethers.toUtf8Bytes("pdf"));
    await expect(registry.connect(issuer).issueCertificate("CERT-2026-000001", hash, 0, "ipfs://metadata"))
      .to.emit(registry, "CertificateIssued");
    const record = await registry.verifyCertificate("CERT-2026-000001");
    expect(record[0]).to.equal(true);
    expect(record[1]).to.equal(hash);
  });

  it("prevents duplicate certificate ids", async function () {
    const { registry, issuer } = await fixture();
    const hash = ethers.keccak256(ethers.toUtf8Bytes("pdf"));
    await registry.connect(issuer).issueCertificate("CERT-2026-000001", hash, 0, "");
    await expect(registry.connect(issuer).issueCertificate("CERT-2026-000001", hash, 0, "")).to.be.revertedWithCustomError(registry, "DuplicateCertificateId");
  });

  it("prevents unapproved issuers and supports revocation", async function () {
    const { registry, issuer, other } = await fixture();
    const hash = ethers.keccak256(ethers.toUtf8Bytes("pdf"));
    await expect(registry.connect(other).issueCertificate("CERT-2026-000002", hash, 0, "")).to.be.reverted;
    await registry.connect(issuer).issueCertificate("CERT-2026-000002", hash, 0, "");
    await registry.connect(issuer).revokeCertificate("CERT-2026-000002");
    const cert = await registry.getCertificate("CERT-2026-000002");
    expect(cert.revoked).to.equal(true);
  });
});
