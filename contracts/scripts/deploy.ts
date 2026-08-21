import { ethers } from "hardhat";

async function main() {
  const [deployer, sampleIssuer] = await ethers.getSigners();
  const Registry = await ethers.getContractFactory("VerifiCertRegistry");
  const registry = await Registry.deploy(deployer.address);
  await registry.waitForDeployment();
  await registry.registerIssuer(sampleIssuer.address);
  console.log("VERIFICERT_CONTRACT_ADDRESS=", await registry.getAddress());
  console.log("ADMIN_WALLET=", deployer.address);
  console.log("SAMPLE_ISSUER_WALLET=", sampleIssuer.address);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
