import { ethers } from "hardhat";

async function main() {
  const [deployer, ...issuers] = await ethers.getSigners();
  const Registry = await ethers.getContractFactory("VerifiCertRegistry");
  const registry = await Registry.deploy(deployer.address);
  await registry.waitForDeployment();
  for (const issuer of issuers.slice(0, 5)) {
    await registry.registerIssuer(issuer.address);
  }
  console.log("VERIFICERT_CONTRACT_ADDRESS=", await registry.getAddress());
  console.log("ADMIN_WALLET=", deployer.address);
  const labels = ["ABC_ACADEMY", "NORTHBRIDGE", "CLOUDSKILLS", "BRIGHTPATH", "TECHBRIDGE"];
  for (const [index, issuer] of issuers.slice(0, 5).entries()) {
    console.log(`${labels[index]}_WALLET_ADDRESS=`, issuer.address);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
