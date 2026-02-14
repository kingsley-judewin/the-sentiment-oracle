/**
 * oracle_bridge.js — AI ↔ Blockchain Automation Bridge
 * ======================================================
 * Autonomous oracle that fetches sentiment from the AI engine
 * and pushes smoothed scores on-chain with safety filters.
 *
 * Usage:
 *   node scripts/oracle_bridge.js              # Production auto-loop
 *   node scripts/oracle_bridge.js --demo       # 3-cycle demo mode
 */

require("dotenv").config();
const hre = require("hardhat");

// ══════════════════════════════════════════════════════
// CONFIGURATION
// ══════════════════════════════════════════════════════

const CONFIG = {
  // Contract
  CONTRACT_ADDRESS: "0x0878645D0ee175Df0a5F61fa047A72d346b1D162",

  // AI Engine
  AI_ENGINE_URL: "http://localhost:8000/oracle",

  // Safety filters
  MIN_SAMPLE_SIZE: 10,
  MIN_SCORE: -100,
  MAX_SCORE: 100,

  // Timing
  UPDATE_INTERVAL_MS: 60_000,    // 60 seconds — aligned with contract rate limit
  FETCH_TIMEOUT_MS: 15_000,      // 15 second timeout for AI engine
  MAX_RETRIES: 3,
  RETRY_BACKOFF_MS: 5_000,       // 5 second base backoff

  // Demo
  DEMO_CYCLES: 3,
};

// ══════════════════════════════════════════════════════
// STATE
// ══════════════════════════════════════════════════════

let lastPushedScore = null;
let cycleCount = 0;
let consecutiveFailures = 0;

// ══════════════════════════════════════════════════════
// LOGGING
// ══════════════════════════════════════════════════════

function log(level, msg, data = {}) {
  const timestamp = new Date().toISOString();
  const prefix = { INFO: "[INFO]", WARN: "[WARN]", ERROR: "[ERR ]", OK: "[ OK ]" }[level] || "[???]";
  const extra = Object.keys(data).length > 0 ? " " + JSON.stringify(data) : "";
  console.log(`${timestamp} ${prefix} ${msg}${extra}`);
}

// ══════════════════════════════════════════════════════
// AI ENGINE FETCH
// ══════════════════════════════════════════════════════

async function fetchSentiment() {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), CONFIG.FETCH_TIMEOUT_MS);

  try {
    const response = await fetch(CONFIG.AI_ENGINE_URL, { signal: controller.signal });

    if (!response.ok) {
      throw new Error(`AI engine returned HTTP ${response.status}`);
    }

    const data = await response.json();
    return data;
  } finally {
    clearTimeout(timeout);
  }
}

async function fetchWithRetry() {
  for (let attempt = 1; attempt <= CONFIG.MAX_RETRIES; attempt++) {
    try {
      const data = await fetchSentiment();
      return data;
    } catch (err) {
      log("WARN", `Fetch attempt ${attempt}/${CONFIG.MAX_RETRIES} failed: ${err.message}`);

      if (attempt < CONFIG.MAX_RETRIES) {
        const backoff = CONFIG.RETRY_BACKOFF_MS * attempt;
        log("INFO", `Retrying in ${backoff / 1000}s...`);
        await sleep(backoff);
      }
    }
  }

  throw new Error(`AI engine unreachable after ${CONFIG.MAX_RETRIES} attempts`);
}

// ══════════════════════════════════════════════════════
// SAFETY FILTERS
// ══════════════════════════════════════════════════════

function validatePayload(data) {
  const errors = [];

  // Must have smoothed_score
  if (data.smoothed_score === undefined || data.smoothed_score === null) {
    errors.push("Missing smoothed_score");
  }

  // Score must be numeric
  if (typeof data.smoothed_score !== "number") {
    errors.push(`smoothed_score is not a number: ${typeof data.smoothed_score}`);
  }

  // Score must be within bounds
  const score = Math.round(data.smoothed_score);
  if (score < CONFIG.MIN_SCORE || score > CONFIG.MAX_SCORE) {
    errors.push(`Score ${score} out of bounds [${CONFIG.MIN_SCORE}, ${CONFIG.MAX_SCORE}]`);
  }

  // Sample size check
  if (data.post_count !== undefined && data.post_count < CONFIG.MIN_SAMPLE_SIZE) {
    errors.push(`Sample size ${data.post_count} below minimum ${CONFIG.MIN_SAMPLE_SIZE}`);
  }

  return { valid: errors.length === 0, errors, score };
}

function shouldPush(score) {
  // Reject duplicate score (aligned with contract replay protection)
  if (score === lastPushedScore) {
    log("INFO", "Score unchanged from last push, skipping", { score, lastPushed: lastPushedScore });
    return false;
  }

  return true;
}

// ══════════════════════════════════════════════════════
// ON-CHAIN PUSH
// ══════════════════════════════════════════════════════

async function pushToChain(contract, score) {
  log("INFO", "Sending transaction...", { score });

  const tx = await contract.updateSentiment(score);
  const receipt = await tx.wait();

  const result = {
    txHash: receipt.hash,
    gasUsed: receipt.gasUsed.toString(),
    blockNumber: receipt.blockNumber,
  };

  log("OK", "Transaction confirmed", result);
  return result;
}

async function readOnChainState(contract) {
  const [currentScore, lastUpdatedAt, isBullish, isBearish] = await contract.getOracleState();
  return {
    currentScore: Number(currentScore),
    lastUpdatedAt: Number(lastUpdatedAt),
    isBullish,
    isBearish,
  };
}

// ══════════════════════════════════════════════════════
// ORACLE CYCLE
// ══════════════════════════════════════════════════════

async function runCycle(contract) {
  cycleCount++;
  log("INFO", `── Cycle ${cycleCount} ──────────────────────────────`);

  // 1. Fetch sentiment from AI engine
  let data;
  try {
    data = await fetchWithRetry();
    log("INFO", "AI engine response received", {
      raw: data.raw_score,
      smoothed: data.smoothed_score,
      posts: data.post_count,
    });
  } catch (err) {
    consecutiveFailures++;
    log("ERROR", `Fetch failed: ${err.message}`, { consecutiveFailures });
    return { pushed: false, reason: "fetch_failed" };
  }

  // 2. Validate payload
  const validation = validatePayload(data);
  if (!validation.valid) {
    log("WARN", "Payload rejected by safety filters", { errors: validation.errors });
    return { pushed: false, reason: "validation_failed", errors: validation.errors };
  }

  const score = validation.score;

  // 3. Check if push is needed
  if (!shouldPush(score)) {
    return { pushed: false, reason: "duplicate_score" };
  }

  // 4. Read current on-chain state for comparison
  try {
    const onChainState = await readOnChainState(contract);
    log("INFO", "Current on-chain state", onChainState);

    // Double-check against on-chain value
    if (score === onChainState.currentScore) {
      log("INFO", "Score already matches on-chain, skipping");
      lastPushedScore = score;
      return { pushed: false, reason: "already_on_chain" };
    }
  } catch (err) {
    log("WARN", `Could not read on-chain state: ${err.message} — proceeding with push`);
  }

  // 5. Push to chain
  try {
    const txResult = await pushToChain(contract, score);
    lastPushedScore = score;
    consecutiveFailures = 0;

    // 6. Read updated state
    const newState = await readOnChainState(contract);
    const signal = newState.isBullish ? "BULLISH" : newState.isBearish ? "BEARISH" : "NEUTRAL";
    log("OK", `Signal: ${signal}`, { score: newState.currentScore });

    return { pushed: true, score, signal, ...txResult };
  } catch (err) {
    consecutiveFailures++;
    log("ERROR", `Transaction failed: ${err.message}`, { consecutiveFailures });
    return { pushed: false, reason: "tx_failed", error: err.message };
  }
}

// ══════════════════════════════════════════════════════
// UTILITIES
// ══════════════════════════════════════════════════════

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ══════════════════════════════════════════════════════
// DEMO MODE
// ══════════════════════════════════════════════════════

async function runDemo(contract) {
  console.log("\n" + "=".repeat(50));
  console.log("  SENTIMENT ORACLE — Demo Mode");
  console.log("=".repeat(50));
  console.log(`  Running ${CONFIG.DEMO_CYCLES} update cycles`);
  console.log("=".repeat(50) + "\n");

  const results = [];

  for (let i = 0; i < CONFIG.DEMO_CYCLES; i++) {
    if (i > 0) {
      log("INFO", "Waiting for rate limit window...");
      await sleep(CONFIG.UPDATE_INTERVAL_MS + 2000); // +2s buffer for block timestamp
    }

    const result = await runCycle(contract);
    results.push(result);
  }

  // Summary
  console.log("\n" + "=".repeat(50));
  console.log("  DEMO RESULTS");
  console.log("=".repeat(50));

  const pushed = results.filter((r) => r.pushed).length;
  const skipped = results.filter((r) => !r.pushed).length;

  console.log(`  Cycles:  ${CONFIG.DEMO_CYCLES}`);
  console.log(`  Pushed:  ${pushed}`);
  console.log(`  Skipped: ${skipped}`);

  for (let i = 0; i < results.length; i++) {
    const r = results[i];
    if (r.pushed) {
      console.log(`  [${i + 1}] Score ${r.score} → ${r.signal} (tx: ${r.txHash.slice(0, 14)}...)`);
    } else {
      console.log(`  [${i + 1}] Skipped: ${r.reason}`);
    }
  }

  // Final on-chain state
  const finalState = await readOnChainState(contract);
  console.log("\n  Final On-Chain State:");
  console.log(`    Score:    ${finalState.currentScore}`);
  console.log(`    Bullish:  ${finalState.isBullish}`);
  console.log(`    Bearish:  ${finalState.isBearish}`);
  console.log("=".repeat(50));
}

// ══════════════════════════════════════════════════════
// PRODUCTION LOOP
// ══════════════════════════════════════════════════════

async function runLoop(contract) {
  console.log("\n" + "=".repeat(50));
  console.log("  SENTIMENT ORACLE — Production Bridge");
  console.log("=".repeat(50));
  console.log(`  Contract:  ${CONFIG.CONTRACT_ADDRESS}`);
  console.log(`  AI Engine: ${CONFIG.AI_ENGINE_URL}`);
  console.log(`  Interval:  ${CONFIG.UPDATE_INTERVAL_MS / 1000}s`);
  console.log(`  Min Posts:  ${CONFIG.MIN_SAMPLE_SIZE}`);
  console.log("=".repeat(50) + "\n");

  // Initial cycle
  await runCycle(contract);

  // Auto-loop
  setInterval(async () => {
    try {
      await runCycle(contract);
    } catch (err) {
      log("ERROR", `Unhandled error in cycle: ${err.message}`);
    }
  }, CONFIG.UPDATE_INTERVAL_MS);
}

// ══════════════════════════════════════════════════════
// ENTRY POINT
// ══════════════════════════════════════════════════════

async function main() {
  const [signer] = await hre.ethers.getSigners();
  log("INFO", "Oracle signer loaded", { address: signer.address });

  const contract = await hre.ethers.getContractAt(
    "SentimentOracle",
    CONFIG.CONTRACT_ADDRESS,
    signer
  );
  log("INFO", "Contract connected", { address: CONFIG.CONTRACT_ADDRESS });

  const isDemo = process.argv.includes("--demo");

  if (isDemo) {
    await runDemo(contract);
  } else {
    await runLoop(contract);
  }
}

main().catch((error) => {
  console.error("\nFATAL:", error.message);
  process.exit(1);
});
