const hre = require("hardhat");

async function main() {
  const contractAddress = "0x0878645D0ee175Df0a5F61fa047A72d346b1D162";

  const oracle = await hre.ethers.getContractAt(
    "SentimentOracle",
    contractAddress
  );

  const score = parseInt(process.argv[2]) || 75;

  console.log("Sending sentiment score:", score);

  const tx = await oracle.updateSentiment(score);
  await tx.wait();

  console.log("Transaction Hash:", tx.hash);

  // Read full oracle state
  const [currentScore, lastUpdatedAt, isBullish, isBearish] = await oracle.getOracleState();

  console.log("\nOracle State:");
  console.log("  Score:", currentScore.toString());
  console.log("  Last Updated:", lastUpdatedAt.toString());
  console.log("  Bullish:", isBullish);
  console.log("  Bearish:", isBearish);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
