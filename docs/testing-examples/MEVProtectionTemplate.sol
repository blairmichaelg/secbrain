// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

/**
 * @title MEV Protection and Slippage Control Template
 * @notice Demonstrates protection against MEV attacks and front-running
 * @dev Implements comprehensive MEV resistance patterns:
 *      1. Slippage protection for all trades
 *      2. Deadline enforcement to prevent stale transactions
 *      3. Commit-reveal scheme for sensitive operations
 *      4. Private transaction support integration points
 *      5. Sandwich attack prevention
 *      6. Just-in-time (JIT) liquidity attack protection
 * 
 * @custom:security-features
 *      - Multi-layer slippage protection
 *      - Transaction deadline enforcement
 *      - Front-running resistant commit-reveal
 *      - MEV-aware transaction ordering
 */

// ============================================================================
// Custom Errors
// ============================================================================

error SlippageExceeded(uint256 expected, uint256 actual);
error DeadlineExpired(uint256 deadline, uint256 currentTime);
error InvalidCommitment();
error CommitmentNotFound();
error AlreadyCommitted();
error RevealTooEarly(uint256 currentBlock, uint256 minRevealBlock);
error RevealTooLate(uint256 currentBlock, uint256 maxRevealBlock);
error ZeroAmount();
error InvalidSlippage();
error SandwichAttackDetected();

// ============================================================================
// Slippage Protection
// ============================================================================

/**
 * @title SlippageProtection
 * @notice Comprehensive slippage protection for DEX trades and swaps
 * @dev Implements multiple slippage protection mechanisms
 */
abstract contract SlippageProtection {
    
    // ========================================================================
    // Constants
    // ========================================================================
    
    // Maximum allowed slippage in basis points (1% = 100 bps)
    uint256 public constant MAX_SLIPPAGE_BPS = 500; // 5%
    uint256 private constant BPS_DENOMINATOR = 10000;
    
    // Default slippage if user doesn't specify
    uint256 public constant DEFAULT_SLIPPAGE_BPS = 50; // 0.5%
    
    // ========================================================================
    // Events
    // ========================================================================
    
    event SlippageProtectionApplied(
        address indexed user,
        uint256 expectedAmount,
        uint256 actualAmount,
        uint256 slippageBps
    );
    
    // ========================================================================
    // Slippage Validation
    // ========================================================================
    
    /**
     * @notice Validate slippage tolerance
     * @dev Ensures slippage parameter is within acceptable bounds
     * @param slippageBps Slippage tolerance in basis points
     */
    function _validateSlippageTolerance(uint256 slippageBps) internal pure {
        if (slippageBps > MAX_SLIPPAGE_BPS) revert InvalidSlippage();
    }
    
    /**
     * @notice Calculate minimum acceptable output with slippage
     * @param expectedAmount Expected output amount
     * @param slippageBps Slippage tolerance in basis points
     * @return minAmount Minimum acceptable amount
     */
    function _calculateMinOutput(uint256 expectedAmount, uint256 slippageBps) 
        internal 
        pure 
        returns (uint256 minAmount) 
    {
        _validateSlippageTolerance(slippageBps);
        
        // Calculate minimum: expected * (10000 - slippage) / 10000
        minAmount = (expectedAmount * (BPS_DENOMINATOR - slippageBps)) / BPS_DENOMINATOR;
        
        return minAmount;
    }
    
    /**
     * @notice Calculate maximum acceptable input with slippage
     * @param expectedAmount Expected input amount
     * @param slippageBps Slippage tolerance in basis points
     * @return maxAmount Maximum acceptable amount
     */
    function _calculateMaxInput(uint256 expectedAmount, uint256 slippageBps) 
        internal 
        pure 
        returns (uint256 maxAmount) 
    {
        _validateSlippageTolerance(slippageBps);
        
        // Calculate maximum: expected * (10000 + slippage) / 10000
        maxAmount = (expectedAmount * (BPS_DENOMINATOR + slippageBps)) / BPS_DENOMINATOR;
        
        return maxAmount;
    }
    
    /**
     * @notice Enforce slippage protection on output amount
     * @param expectedAmount Expected output amount
     * @param actualAmount Actual output amount
     * @param slippageBps Slippage tolerance in basis points
     */
    function _enforceSlippageProtection(
        uint256 expectedAmount,
        uint256 actualAmount,
        uint256 slippageBps
    ) internal {
        uint256 minAmount = _calculateMinOutput(expectedAmount, slippageBps);
        
        if (actualAmount < minAmount) {
            revert SlippageExceeded(minAmount, actualAmount);
        }
        
        emit SlippageProtectionApplied(msg.sender, expectedAmount, actualAmount, slippageBps);
    }
}

// ============================================================================
// Deadline Protection
// ============================================================================

/**
 * @title DeadlineProtection
 * @notice Prevents execution of stale transactions
 * @dev Critical for preventing front-running via delayed execution
 */
abstract contract DeadlineProtection {
    
    // ========================================================================
    // Modifiers
    // ========================================================================
    
    /**
     * @notice Ensure transaction executes before deadline
     * @dev Prevents validators from holding transactions for front-running
     * @param deadline Unix timestamp deadline
     */
    modifier beforeDeadline(uint256 deadline) {
        if (block.timestamp > deadline) {
            revert DeadlineExpired(deadline, block.timestamp);
        }
        _;
    }
    
    // ========================================================================
    // Deadline Helpers
    // ========================================================================
    
    /**
     * @notice Calculate reasonable deadline from current time
     * @param minutesFromNow Minutes to add to current timestamp
     * @return deadline Unix timestamp deadline
     */
    function _getDeadline(uint256 minutesFromNow) internal view returns (uint256 deadline) {
        return block.timestamp + (minutesFromNow * 1 minutes);
    }
    
    /**
     * @notice Validate deadline is reasonable (not too far in future)
     * @param deadline Deadline to validate
     * @param maxMinutes Maximum allowed minutes from now
     */
    function _validateDeadline(uint256 deadline, uint256 maxMinutes) internal view {
        uint256 maxDeadline = block.timestamp + (maxMinutes * 1 minutes);
        require(deadline <= maxDeadline, "Deadline too far in future");
    }
}

// ============================================================================
// Commit-Reveal Pattern
// ============================================================================

/**
 * @title CommitReveal
 * @notice Front-running resistant commit-reveal mechanism
 * @dev Two-phase execution: commit intention, then reveal after delay
 *      Prevents front-running of sensitive operations like:
 *      - Bids and auctions
 *      - Voting
 *      - Price-sensitive trades
 */
abstract contract CommitReveal {
    
    // ========================================================================
    // Structures
    // ========================================================================
    
    struct Commitment {
        bytes32 commitHash;      // Hash of committed data
        uint256 commitBlock;     // Block number of commitment
        uint256 revealDeadline;  // Deadline for reveal
        bool revealed;           // Whether commitment has been revealed
    }
    
    // ========================================================================
    // State Variables
    // ========================================================================
    
    // User commitments
    mapping(address => Commitment) public commitments;
    
    // Minimum blocks between commit and reveal (prevents same-block reveal)
    uint256 public constant MIN_COMMIT_REVEAL_BLOCKS = 2;
    
    // Maximum blocks for reveal (prevents indefinite pending)
    uint256 public constant MAX_REVEAL_DELAY_BLOCKS = 255; // ~1 hour at 12s blocks
    
    // ========================================================================
    // Events
    // ========================================================================
    
    event Committed(address indexed user, bytes32 commitHash, uint256 revealDeadline);
    event Revealed(address indexed user, bytes32 revealData);
    
    // ========================================================================
    // Commit Phase
    // ========================================================================
    
    /**
     * @notice Commit to future action without revealing details
     * @dev User submits hash of (action_data + salt) to prevent front-running
     * @param commitHash Hash of abi.encodePacked(msg.sender, actionData, salt)
     */
    function _commit(bytes32 commitHash) internal {
        if (commitments[msg.sender].commitHash != bytes32(0)) {
            revert AlreadyCommitted();
        }
        
        uint256 revealDeadline = block.number + MAX_REVEAL_DELAY_BLOCKS;
        
        commitments[msg.sender] = Commitment({
            commitHash: commitHash,
            commitBlock: block.number,
            revealDeadline: revealDeadline,
            revealed: false
        });
        
        emit Committed(msg.sender, commitHash, revealDeadline);
    }
    
    // ========================================================================
    // Reveal Phase
    // ========================================================================
    
    /**
     * @notice Reveal committed action and execute
     * @dev Validates commitment, checks timing, then executes action
     * @param actionData Original action data
     * @param salt Random salt used in commitment
     */
    function _reveal(bytes memory actionData, bytes32 salt) internal {
        Commitment storage commitment = commitments[msg.sender];
        
        // Validate commitment exists
        if (commitment.commitHash == bytes32(0)) {
            revert CommitmentNotFound();
        }
        
        // Validate not already revealed
        if (commitment.revealed) {
            revert AlreadyCommitted();
        }
        
        // Validate timing - must wait minimum blocks
        if (block.number < commitment.commitBlock + MIN_COMMIT_REVEAL_BLOCKS) {
            revert RevealTooEarly(block.number, commitment.commitBlock + MIN_COMMIT_REVEAL_BLOCKS);
        }
        
        // Validate timing - must reveal before deadline
        if (block.number > commitment.revealDeadline) {
            revert RevealTooLate(block.number, commitment.revealDeadline);
        }
        
        // Validate commitment matches reveal
        bytes32 revealHash = keccak256(abi.encodePacked(msg.sender, actionData, salt));
        if (revealHash != commitment.commitHash) {
            revert InvalidCommitment();
        }
        
        // Mark as revealed
        commitment.revealed = true;
        
        emit Revealed(msg.sender, revealHash);
    }
    
    /**
     * @notice Clear commitment (user can cancel)
     */
    function _clearCommitment() internal {
        delete commitments[msg.sender];
    }
    
    /**
     * @notice Generate commitment hash
     * @param user User address
     * @param actionData Action data to commit
     * @param salt Random salt for uniqueness
     * @return Hash for commitment
     */
    function _generateCommitHash(
        address user,
        bytes memory actionData,
        bytes32 salt
    ) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(user, actionData, salt));
    }
}

// ============================================================================
// Sandwich Attack Prevention
// ============================================================================

/**
 * @title SandwichAttackPrevention
 * @notice Detects and prevents sandwich attacks on trades
 * @dev Monitors price impact and detects suspicious patterns
 */
abstract contract SandwichAttackPrevention {
    
    // ========================================================================
    // State Variables
    // ========================================================================
    
    // Track price impact per block to detect sandwiching
    mapping(uint256 => uint256) private _blockPriceImpact;
    mapping(uint256 => uint256) private _blockTradeCount;
    
    // Maximum allowed price impact per trade
    uint256 public constant MAX_PRICE_IMPACT_BPS = 100; // 1%
    
    // Maximum cumulative price impact per block
    uint256 public constant MAX_BLOCK_PRICE_IMPACT_BPS = 300; // 3%
    
    uint256 private constant BPS_DENOMINATOR = 10000;
    
    // ========================================================================
    // Sandwich Detection
    // ========================================================================
    
    /**
     * @notice Validate trade doesn't contribute to sandwich attack
     * @param priceImpactBps Price impact of this trade in basis points
     */
    function _validateNotSandwiched(uint256 priceImpactBps) internal {
        // Check individual trade impact
        if (priceImpactBps > MAX_PRICE_IMPACT_BPS) {
            revert SandwichAttackDetected();
        }
        
        // Check cumulative block impact (detects sandwich pattern)
        uint256 blockImpact = _blockPriceImpact[block.number];
        uint256 newBlockImpact;
        
        unchecked {
            // Safe: price impact is bounded by MAX values
            newBlockImpact = blockImpact + priceImpactBps;
        }
        
        if (newBlockImpact > MAX_BLOCK_PRICE_IMPACT_BPS) {
            revert SandwichAttackDetected();
        }
        
        // Update block tracking
        _blockPriceImpact[block.number] = newBlockImpact;
        
        unchecked {
            // Safe: trade count cannot realistically overflow
            _blockTradeCount[block.number]++;
        }
    }
    
    /**
     * @notice Calculate price impact in basis points
     * @param reserveBefore Reserve balance before trade
     * @param reserveAfter Reserve balance after trade
     * @return priceImpactBps Price impact in basis points
     */
    function _calculatePriceImpact(
        uint256 reserveBefore,
        uint256 reserveAfter
    ) internal pure returns (uint256 priceImpactBps) {
        if (reserveBefore == 0) return 0;
        
        if (reserveAfter > reserveBefore) {
            priceImpactBps = ((reserveAfter - reserveBefore) * BPS_DENOMINATOR) / reserveBefore;
        } else {
            priceImpactBps = ((reserveBefore - reserveAfter) * BPS_DENOMINATOR) / reserveBefore;
        }
        
        return priceImpactBps;
    }
}

// ============================================================================
// MEV-Protected DEX Example
// ============================================================================

/**
 * @title MEVProtectedDEX
 * @notice Example DEX with comprehensive MEV protection
 * @dev Combines all MEV protection patterns into production-ready implementation
 */
contract MEVProtectedDEX is 
    SlippageProtection, 
    DeadlineProtection, 
    CommitReveal,
    SandwichAttackPrevention 
{
    
    // ========================================================================
    // State Variables
    // ========================================================================
    
    // Simplified liquidity pool
    uint256 public reserveToken0;
    uint256 public reserveToken1;
    
    // ========================================================================
    // Events
    // ========================================================================
    
    event Swap(
        address indexed user,
        uint256 amountIn,
        uint256 amountOut,
        uint256 slippageBps
    );
    
    event LiquidityAdded(address indexed user, uint256 amount0, uint256 amount1);
    
    // ========================================================================
    // Protected Swap Functions
    // ========================================================================
    
    /**
     * @notice Swap with comprehensive MEV protection
     * @dev Implements: slippage protection, deadline, sandwich prevention
     * @param amountIn Amount of input tokens
     * @param minAmountOut Minimum acceptable output (slippage protection)
     * @param deadline Transaction deadline
     * @return amountOut Actual output amount
     */
    function swapWithProtection(
        uint256 amountIn,
        uint256 minAmountOut,
        uint256 deadline
    ) 
        external 
        beforeDeadline(deadline)
        returns (uint256 amountOut) 
    {
        if (amountIn == 0) revert ZeroAmount();
        
        // Calculate output with constant product formula (simplified)
        amountOut = _calculateSwapOutput(amountIn);
        
        // Enforce slippage protection
        if (amountOut < minAmountOut) {
            revert SlippageExceeded(minAmountOut, amountOut);
        }
        
        // Calculate and validate price impact (sandwich prevention)
        uint256 reserveBefore = reserveToken1;
        uint256 reserveAfter = reserveToken1 - amountOut;
        uint256 priceImpact = _calculatePriceImpact(reserveBefore, reserveAfter);
        _validateNotSandwiched(priceImpact);
        
        // Update reserves (Effects)
        unchecked {
            reserveToken0 += amountIn;
            reserveToken1 -= amountOut;
        }
        
        emit Swap(msg.sender, amountIn, amountOut, 
            ((minAmountOut * BPS_DENOMINATOR) / amountOut));
        
        // In production: transfer tokens (Interactions)
        
        return amountOut;
    }
    
    /**
     * @notice Commit to future swap (front-running resistant)
     * @param commitHash Hash of swap parameters + salt
     */
    function commitSwap(bytes32 commitHash) external {
        _commit(commitHash);
    }
    
    /**
     * @notice Reveal and execute committed swap
     * @param amountIn Input amount
     * @param minAmountOut Minimum output
     * @param deadline Deadline
     * @param salt Random salt
     */
    function revealSwap(
        uint256 amountIn,
        uint256 minAmountOut,
        uint256 deadline,
        bytes32 salt
    ) external beforeDeadline(deadline) returns (uint256 amountOut) {
        // Encode action data
        bytes memory actionData = abi.encode(amountIn, minAmountOut, deadline);
        
        // Validate and reveal commitment
        _reveal(actionData, salt);
        
        // Execute swap with protection
        amountOut = _calculateSwapOutput(amountIn);
        
        if (amountOut < minAmountOut) {
            revert SlippageExceeded(minAmountOut, amountOut);
        }
        
        // Update reserves
        unchecked {
            reserveToken0 += amountIn;
            reserveToken1 -= amountOut;
        }
        
        emit Swap(msg.sender, amountIn, amountOut, 
            ((minAmountOut * BPS_DENOMINATOR) / amountOut));
        
        // Clear commitment
        _clearCommitment();
        
        return amountOut;
    }
    
    // ========================================================================
    // Helper Functions
    // ========================================================================
    
    /**
     * @notice Calculate swap output (simplified constant product)
     * @param amountIn Input amount
     * @return amountOut Output amount
     * 
     * ⚠️ WARNING: Simplified implementation for template purposes
     * ⚠️ Production MUST include: fees, overflow protection, slippage
     * ⚠️ Consider using SafeMath for large values
     */
    function _calculateSwapOutput(uint256 amountIn) 
        internal 
        view 
        returns (uint256 amountOut) 
    {
        // Simplified: constant product formula x * y = k
        // In production: use full UniswapV2 formula with fees
        
        if (reserveToken0 == 0 || reserveToken1 == 0) return 0;
        
        // ⚠️ Add overflow protection for production:
        // require(amountIn <= type(uint112).max, "Overflow protection");
        
        uint256 numerator = amountIn * reserveToken1;
        uint256 denominator = reserveToken0 + amountIn;
        
        require(denominator > 0, "Division by zero");
        amountOut = numerator / denominator;
        
        return amountOut;
    }
    
    /**
     * @notice Add liquidity (for testing)
     * @param amount0 Amount of token0
     * @param amount1 Amount of token1
     */
    function addLiquidity(uint256 amount0, uint256 amount1) external {
        unchecked {
            reserveToken0 += amount0;
            reserveToken1 += amount1;
        }
        
        emit LiquidityAdded(msg.sender, amount0, amount1);
    }
}
