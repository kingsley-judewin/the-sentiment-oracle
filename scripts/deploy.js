const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();

  console.log("=".repeat(50));
  console.log("  SENTIMENT ORACLE — Deployment");
  console.log("=".repeat(50));
  console.log("\nDeployer:", deployer.address);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("Balance:", hre.ethers.formatEther(balance), "MATIC\n");

  // Deploy contract with deployer as oracle
  const SentimentOracle = await hre.ethers.getContractFactory("SentimentOracle");
  const oracleContract = await SentimentOracle.deploy(deployer.address);
  await oracleContract.waitForDeployment();

  const address = await oracleContract.getAddress();

  // Read default configuration
  const bullishThreshold = await oracleContract.bullishThreshold();
  const bearishThreshold = await oracleContract.bearishThreshold();
  const minInterval = await oracleContract.minUpdateInterval();

  console.log("SentimentOracle deployed to:", address);
  console.log("Oracle signer:", deployer.address);
  console.log("\nDefault Configuration:");
  console.log("  Bullish threshold:", bullishThreshold.toString());
  console.log("  Bearish threshold:", bearishThreshold.toString());
  console.log("  Min update interval:", minInterval.toString(), "seconds");
  console.log("\n" + "=".repeat(50));
  console.log("  Update CONTRACT_ADDRESS in oracle_bridge.js");
  console.log("=".repeat(50));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
