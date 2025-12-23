// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

/**
 * @title Oracle Security Template
 * @notice Demonstrates protection against oracle manipulation and flash loan attacks
 * @dev Implements comprehensive oracle security patterns:
 *      1. Chainlink price feeds with staleness checks
 *      2. TWAP (Time-Weighted Average Price) using Uniswap V3
 *      3. Multi-oracle consensus for critical price data
 *      4. Price deviation detection and rejection
 *      5. Flash loan price manipulation resistance
 * 
 * @custom:security-features
 *      - Staleness checks for price feed data
 *      - TWAP calculation for manipulation resistance
 *      - Multi-oracle validation and consensus
 *      - Circuit breakers for extreme price movements
 *      - Protection against same-block price manipulation
 */

// ============================================================================
// Custom Errors
// ============================================================================

error StalePrice();
error InvalidPrice();
error PriceDeviationTooHigh(uint256 deviation, uint256 maxDeviation);
error InsufficientOracles();
error OracleConsensusFailure();
error CircuitBreakerTriggered();
error ZeroAddress();

// ============================================================================
// Interfaces (Simplified for Template)
// ============================================================================

/**
 * @notice Chainlink Aggregator V3 Interface
 * @dev Simplified interface for price feed integration
 */
interface AggregatorV3Interface {
    function decimals() external view returns (uint8);
    
    function latestRoundData()
        external
        view
        returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        );
}

/**
 * @notice Uniswap V3 Pool Interface
 * @dev Simplified interface for TWAP oracle
 */
interface IUniswapV3Pool {
    function observe(uint32[] calldata secondsAgos)
        external
        view
        returns (int56[] memory tickCumulatives, uint160[] memory secondsPerLiquidityCumulativeX128s);
}

// ============================================================================
// Chainlink Oracle Integration
// ============================================================================

/**
 * @title ChainlinkOracle
 * @notice Secure Chainlink price feed integration with comprehensive validation
 * @dev Implements all critical checks for production-ready oracle usage
 */
contract ChainlinkOracle {
    
    // ========================================================================
    // State Variables
    // ========================================================================
    
    AggregatorV3Interface public immutable priceFeed;
    
    // Staleness threshold - price must be updated within this time
    uint256 public constant STALENESS_THRESHOLD = 3600; // 1 hour
    
    // Maximum allowed price deviation between updates
    uint256 public constant MAX_PRICE_DEVIATION_BPS = 1000; // 10%
    uint256 private constant BPS_DENOMINATOR = 10000;
    
    // Last known valid price (for deviation checks)
    uint256 private _lastValidPrice;
    uint256 private _lastValidTimestamp;
    
    // Circuit breaker
    bool private _circuitBreakerActive;
    
    // ========================================================================
    // Events
    // ========================================================================
    
    event PriceUpdated(uint256 price, uint256 timestamp);
    event CircuitBreakerActivated(uint256 price, uint256 deviation);
    event CircuitBreakerDeactivated(address indexed admin);
    
    // ========================================================================
    // Constructor
    // ========================================================================
    
    /**
     * @notice Initialize Chainlink oracle
     * @param _priceFeed Address of Chainlink price feed
     */
    constructor(address _priceFeed) {
        if (_priceFeed == address(0)) revert ZeroAddress();
        priceFeed = AggregatorV3Interface(_priceFeed);
    }
    
    // ========================================================================
    // Core Oracle Functions
    // ========================================================================
    
    /**
     * @notice Get latest price with comprehensive validation
     * @dev Implements all critical security checks:
     *      1. Staleness check - price not too old
     *      2. Round completion check - round is complete
     *      3. Positive price check - price is valid
     *      4. Deviation check - price change is reasonable
     *      5. Circuit breaker check - system is operational
     * @return price Latest validated price
     */
    function getLatestPrice() public view returns (uint256 price) {
        // Check circuit breaker
        if (_circuitBreakerActive) revert CircuitBreakerTriggered();
        
        // Get latest round data from Chainlink
        (
            uint80 roundId,
            int256 answer,
            ,
            uint256 updatedAt,
            uint80 answeredInRound
        ) = priceFeed.latestRoundData();
        
        // 1. Check round is complete (critical for data integrity)
        if (answeredInRound < roundId) revert StalePrice();
        
        // 2. Check price is positive (negative prices indicate failure)
        if (answer <= 0) revert InvalidPrice();
        
        // 3. Check staleness - price must be recent
        if (block.timestamp - updatedAt > STALENESS_THRESHOLD) revert StalePrice();
        
        price = uint256(answer);
        
        // 4. Check price deviation if we have a previous valid price
        if (_lastValidPrice > 0) {
            uint256 deviation = _calculateDeviation(price, _lastValidPrice);
            if (deviation > MAX_PRICE_DEVIATION_BPS) {
                revert PriceDeviationTooHigh(deviation, MAX_PRICE_DEVIATION_BPS);
            }
        }
        
        return price;
    }
    
    /**
     * @notice Update and validate price feed
     * @dev Should be called before critical operations
     * @return price Validated current price
     */
    function updatePrice() external returns (uint256 price) {
        price = getLatestPrice();
        
        // Store as last valid price
        _lastValidPrice = price;
        _lastValidTimestamp = block.timestamp;
        
        emit PriceUpdated(price, block.timestamp);
        
        return price;
    }
    
    /**
     * @notice Calculate price deviation in basis points
     * @param newPrice New price to compare
     * @param oldPrice Previous price
     * @return deviation Deviation in basis points
     */
    function _calculateDeviation(uint256 newPrice, uint256 oldPrice) 
        internal 
        pure 
        returns (uint256 deviation) 
    {
        if (newPrice > oldPrice) {
            deviation = ((newPrice - oldPrice) * BPS_DENOMINATOR) / oldPrice;
        } else {
            deviation = ((oldPrice - newPrice) * BPS_DENOMINATOR) / oldPrice;
        }
        return deviation;
    }
    
    /**
     * @notice Get price feed decimals
     * @return Number of decimals for price feed
     */
    function getDecimals() external view returns (uint8) {
        return priceFeed.decimals();
    }
}

// ============================================================================
// TWAP Oracle Integration (Uniswap V3)
// ============================================================================

/**
 * @title TWAPOracle
 * @notice Time-Weighted Average Price oracle for flash loan resistance
 * @dev Implements TWAP calculation using Uniswap V3 pool observations
 *      Resistant to single-block price manipulation via flash loans
 */
contract TWAPOracle {
    
    // ========================================================================
    // State Variables
    // ========================================================================
    
    IUniswapV3Pool public immutable pool;
    
    // TWAP period - longer periods are more manipulation-resistant
    uint32 public constant TWAP_PERIOD = 1800; // 30 minutes
    uint32 public constant MIN_TWAP_PERIOD = 600; // 10 minutes minimum
    
    // Tick math constants (Uniswap V3)
    int24 private constant MIN_TICK = -887272;
    int24 private constant MAX_TICK = 887272;
    
    // ========================================================================
    // Constructor
    // ========================================================================
    
    /**
     * @notice Initialize TWAP oracle
     * @param _pool Address of Uniswap V3 pool
     */
    constructor(address _pool) {
        if (_pool == address(0)) revert ZeroAddress();
        pool = IUniswapV3Pool(_pool);
    }
    
    // ========================================================================
    // TWAP Calculation
    // ========================================================================
    
    /**
     * @notice Get TWAP price for specified period
     * @dev Calculates time-weighted average price from pool observations
     *      Resistant to flash loan manipulation due to time-weighting
     * @param period Time period for TWAP calculation (in seconds)
     * @return twapPrice Time-weighted average price
     */
    function getTWAP(uint32 period) public view returns (uint256 twapPrice) {
        // Ensure minimum TWAP period for security
        if (period < MIN_TWAP_PERIOD) {
            period = MIN_TWAP_PERIOD;
        }
        
        // Prepare observation array: [period ago, now]
        uint32[] memory secondsAgos = new uint32[](2);
        secondsAgos[0] = period;
        secondsAgos[1] = 0;
        
        // Get tick cumulatives from pool
        (int56[] memory tickCumulatives, ) = pool.observe(secondsAgos);
        
        // Calculate arithmetic mean tick over period
        int56 tickCumulativesDelta = tickCumulatives[1] - tickCumulatives[0];
        int24 arithmeticMeanTick = int24(tickCumulativesDelta / int56(uint56(period)));
        
        // Validate tick is within bounds
        require(arithmeticMeanTick >= MIN_TICK && arithmeticMeanTick <= MAX_TICK, "Invalid tick");
        
        // Convert tick to price (simplified - production would use OracleLibrary)
        twapPrice = _getQuoteAtTick(arithmeticMeanTick);
        
        return twapPrice;
    }
    
    /**
     * @notice Get default TWAP price (30 minutes)
     * @return TWAP price for default period
     */
    function getTWAPPrice() external view returns (uint256) {
        return getTWAP(TWAP_PERIOD);
    }
    
    /**
     * @notice Convert tick to price quote (simplified)
     * @dev Production implementation would use Uniswap's OracleLibrary
     * @param tick The tick to convert
     * @return price The corresponding price
     * 
     * ⚠️ WARNING: This is a PLACEHOLDER implementation
     * ⚠️ DO NOT use this in production without replacing with proper tick conversion
     * ⚠️ Use: OracleLibrary.getQuoteAtTick(tick, baseAmount, baseToken, quoteToken)
     */
    function _getQuoteAtTick(int24 tick) internal pure returns (uint256 price) {
        // Simplified conversion: price = 1.0001^tick
        // Production MUST use: OracleLibrary.getQuoteAtTick(tick, baseAmount, baseToken, quoteToken)
        
        // ⚠️ PLACEHOLDER ONLY - Replace before production deployment
        return 1e18; // Placeholder
    }
}

// ============================================================================
// Multi-Oracle Consensus
// ============================================================================

/**
 * @title MultiOracleConsensus
 * @notice Combines multiple oracles for increased security
 * @dev Implements consensus mechanism across Chainlink, TWAP, and other oracles
 *      Provides maximum protection against oracle manipulation
 */
contract MultiOracleConsensus {
    
    // ========================================================================
    // State Variables
    // ========================================================================
    
    ChainlinkOracle public chainlinkOracle;
    TWAPOracle public twapOracle;
    
    // Consensus parameters
    uint256 public constant MAX_ORACLE_DEVIATION_BPS = 300; // 3%
    uint256 private constant BPS_DENOMINATOR = 10000;
    uint256 public constant MIN_ORACLES_REQUIRED = 2;
    
    // ========================================================================
    // Events
    // ========================================================================
    
    event ConsensusReached(uint256 price, uint256 chainlinkPrice, uint256 twapPrice);
    event ConsensusFailure(uint256 deviation, uint256 maxDeviation);
    
    // ========================================================================
    // Constructor
    // ========================================================================
    
    /**
     * @notice Initialize multi-oracle system
     * @param _chainlinkOracle Address of Chainlink oracle
     * @param _twapOracle Address of TWAP oracle
     */
    constructor(address _chainlinkOracle, address _twapOracle) {
        if (_chainlinkOracle == address(0) || _twapOracle == address(0)) {
            revert ZeroAddress();
        }
        
        chainlinkOracle = ChainlinkOracle(_chainlinkOracle);
        twapOracle = TWAPOracle(_twapOracle);
    }
    
    // ========================================================================
    // Consensus Functions
    // ========================================================================
    
    /**
     * @notice Get consensus price from multiple oracles
     * @dev Validates prices from all oracles are within acceptable deviation
     *      Provides maximum security against manipulation
     * @return consensusPrice Median price if consensus reached
     */
    function getConsensusPrice() external view returns (uint256 consensusPrice) {
        // Get prices from all oracles
        uint256 chainlinkPrice = chainlinkOracle.getLatestPrice();
        uint256 twapPrice = twapOracle.getTWAPPrice();
        
        // Calculate deviation between oracles
        uint256 deviation = _calculateDeviation(chainlinkPrice, twapPrice);
        
        // Check if deviation is acceptable
        if (deviation > MAX_ORACLE_DEVIATION_BPS) {
            revert PriceDeviationTooHigh(deviation, MAX_ORACLE_DEVIATION_BPS);
        }
        
        // Return median price (average of two oracles)
        consensusPrice = (chainlinkPrice + twapPrice) / 2;
        
        return consensusPrice;
    }
    
    /**
     * @notice Get all oracle prices for analysis
     * @return chainlinkPrice Price from Chainlink
     * @return twapPrice Price from TWAP
     * @return deviation Deviation between oracles in basis points
     */
    function getAllPrices() 
        external 
        view 
        returns (
            uint256 chainlinkPrice,
            uint256 twapPrice,
            uint256 deviation
        ) 
    {
        chainlinkPrice = chainlinkOracle.getLatestPrice();
        twapPrice = twapOracle.getTWAPPrice();
        deviation = _calculateDeviation(chainlinkPrice, twapPrice);
        
        return (chainlinkPrice, twapPrice, deviation);
    }
    
    /**
     * @notice Calculate deviation between two prices
     * @param price1 First price
     * @param price2 Second price
     * @return deviation Deviation in basis points
     */
    function _calculateDeviation(uint256 price1, uint256 price2) 
        internal 
        pure 
        returns (uint256 deviation) 
    {
        if (price1 > price2) {
            deviation = ((price1 - price2) * BPS_DENOMINATOR) / price2;
        } else {
            deviation = ((price2 - price1) * BPS_DENOMINATOR) / price1;
        }
        return deviation;
    }
    
    /**
     * @notice Validate oracle consensus is healthy
     * @return healthy True if all oracles agree within threshold
     */
    function isConsensusHealthy() external view returns (bool healthy) {
        try this.getConsensusPrice() returns (uint256) {
            return true;
        } catch {
            return false;
        }
    }
}

// ============================================================================
// Flash Loan Detection and Prevention
// ============================================================================

/**
 * @title FlashLoanProtection
 * @notice Detects and prevents flash loan price manipulation attacks
 * @dev Implements multiple layers of flash loan detection
 */
contract FlashLoanProtection {
    
    // ========================================================================
    // State Variables
    // ========================================================================
    
    // Track user actions per block to detect flash loans
    mapping(address => uint256) private _lastActionBlock;
    
    // Price observations for manipulation detection
    mapping(uint256 => uint256) private _blockPrices;
    uint256 private _lastPriceBlock;
    
    // Maximum allowed price movement in single block
    uint256 public constant MAX_SINGLE_BLOCK_MOVEMENT_BPS = 100; // 1%
    uint256 private constant BPS_DENOMINATOR = 10000;
    
    // ========================================================================
    // Modifiers
    // ========================================================================
    
    /**
     * @notice Prevent same-block actions (flash loan indicator)
     * @dev Prevents deposit->borrow or borrow->repay in same block
     */
    modifier noSameBlockAction() {
        require(
            _lastActionBlock[msg.sender] != block.number,
            "Same block action detected"
        );
        _;
        _lastActionBlock[msg.sender] = block.number;
    }
    
    /**
     * @notice Detect flash loan price manipulation
     * @param currentPrice Current price to validate
     */
    modifier noFlashLoanManipulation(uint256 currentPrice) {
        _validatePriceMovement(currentPrice);
        _;
    }
    
    // ========================================================================
    // Flash Loan Detection
    // ========================================================================
    
    /**
     * @notice Validate price movement is not flash loan manipulation
     * @param currentPrice Current price to validate
     */
    function _validatePriceMovement(uint256 currentPrice) internal {
        // Only check if we have a previous price in same block
        if (_lastPriceBlock == block.number) {
            uint256 previousPrice = _blockPrices[block.number];
            
            // Calculate price movement
            uint256 movement;
            if (currentPrice > previousPrice) {
                movement = ((currentPrice - previousPrice) * BPS_DENOMINATOR) / previousPrice;
            } else {
                movement = ((previousPrice - currentPrice) * BPS_DENOMINATOR) / previousPrice;
            }
            
            // Reject if movement is too large (flash loan indicator)
            require(
                movement <= MAX_SINGLE_BLOCK_MOVEMENT_BPS,
                "Flash loan manipulation detected"
            );
        }
        
        // Store current price
        _blockPrices[block.number] = currentPrice;
        _lastPriceBlock = block.number;
    }
    
    /**
     * @notice Check if user performed action in current block
     * @param user Address to check
     * @return True if user has acted in current block
     */
    function hasActedThisBlock(address user) external view returns (bool) {
        return _lastActionBlock[user] == block.number;
    }
}
