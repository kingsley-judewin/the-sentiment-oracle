require("dotenv").config();
const hre = require("hardhat");

async function main() {
    const CA = "0x0878645D0ee175Df0a5F61fa047A72d346b1D162";
    const c = await hre.ethers.getContractAt("SentimentOracle", CA);

    const score = await c.vibeScore();
    const ts = await c.lastUpdated();
    const oracle = await c.oracle();

    console.log("CONTRACT: " + CA);
    console.log("VIBE_SCORE: " + score.toString());
    console.log("LAST_UPDATED: " + ts.toString());
    console.log("ORACLE: " + oracle);
    console.log("TIMESTAMP: " + new Date(Number(ts) * 1000).toISOString());
}

main().catch(e => { console.log("ERROR: " + e.message); process.exit(1); });
