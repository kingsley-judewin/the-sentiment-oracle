// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SentimentOracle {

    // ==============================
    // STATE VARIABLES
    // ==============================

    int256 public vibeScore;
    uint256 public lastUpdated;
    address public oracle;

    int256 public constant MIN_SCORE = -100;
    int256 public constant MAX_SCORE = 100;

    // ── Threshold Configuration ──
    int256 public bullishThreshold;
    int256 public bearishThreshold;

    // ── Rate Limiting ──
    uint256 public minUpdateInterval;
    uint256 public lastUpdateTimestamp;

    // ==============================
    // EVENTS
    // ==============================

    event OracleUpdated(address indexed oldOracle, address indexed newOracle);
    event SentimentUpdated(
        int256 indexed score,
        uint256 timestamp,
        address indexed updater
    );

    // ── Trigger Events ──
    event BullishSignal(int256 score, uint256 timestamp);
    event BearishSignal(int256 score, uint256 timestamp);
    event NeutralSignal(int256 score, uint256 timestamp);

    // ── Threshold Configuration Events ──
    event ThresholdsUpdated(int256 bullish, int256 bearish);
    event UpdateIntervalChanged(uint256 newInterval);

    // ==============================
    // MODIFIERS
    // ==============================

    modifier onlyOracle() {
        require(msg.sender == oracle, "Not authorized");
        _;
    }

    modifier validScore(int256 _score) {
        require(_score >= MIN_SCORE && _score <= MAX_SCORE, "Score out of range");
        _;
    }

    modifier rateLimited() {
        require(
            block.timestamp - lastUpdateTimestamp >= minUpdateInterval,
            "Update too frequent"
        );
        _;
    }

    // ==============================
    // CONSTRUCTOR
    // ==============================

    constructor(address _oracle) {
        require(_oracle != address(0), "Invalid oracle address");
        oracle = _oracle;

        // Default thresholds
        bullishThreshold = 60;
        bearishThreshold = -60;

        // Default rate limit: 60 seconds
        minUpdateInterval = 60;
        lastUpdateTimestamp = 0;
    }

    // ==============================
    // CORE FUNCTION
    // ==============================

    function updateSentiment(int256 _score)
        external
        onlyOracle
        validScore(_score)
        rateLimited
    {
        // ── Replay Protection ──
        require(_score != vibeScore, "Duplicate score");

        // ── Store State ──
        vibeScore = _score;
        lastUpdated = block.timestamp;
        lastUpdateTimestamp = block.timestamp;

        // ── Emit Core Event ──
        emit SentimentUpdated(_score, block.timestamp, msg.sender);

        // ── Trigger Signal Events ──
        if (_score >= bullishThreshold) {
            emit BullishSignal(_score, block.timestamp);
        } else if (_score <= bearishThreshold) {
            emit BearishSignal(_score, block.timestamp);
        } else {
            emit NeutralSignal(_score, block.timestamp);
        }
    }

    // ==============================
    // ADMIN FUNCTIONS
    // ==============================

    function changeOracle(address _newOracle) external onlyOracle {
        require(_newOracle != address(0), "Invalid address");

        address oldOracle = oracle;
        oracle = _newOracle;

        emit OracleUpdated(oldOracle, _newOracle);
    }

    function setThresholds(int256 _bullish, int256 _bearish) external onlyOracle {
        require(_bullish > _bearish, "Bullish must exceed bearish");
        require(_bullish >= MIN_SCORE && _bullish <= MAX_SCORE, "Bullish out of range");
        require(_bearish >= MIN_SCORE && _bearish <= MAX_SCORE, "Bearish out of range");

        bullishThreshold = _bullish;
        bearishThreshold = _bearish;

        emit ThresholdsUpdated(_bullish, _bearish);
    }

    function setUpdateInterval(uint256 _interval) external onlyOracle {
        minUpdateInterval = _interval;

        emit UpdateIntervalChanged(_interval);
    }

    // ==============================
    // VIEW HELPERS
    // ==============================

    function getSentiment()
        external
        view
        returns (int256 score, uint256 timestamp)
    {
        return (vibeScore, lastUpdated);
    }

    function getOracleState()
        external
        view
        returns (
            int256 currentScore,
            uint256 lastUpdatedAt,
            bool isBullish,
            bool isBearish
        )
    {
        return (
            vibeScore,
            lastUpdated,
            vibeScore >= bullishThreshold,
            vibeScore <= bearishThreshold
        );
    }
}
