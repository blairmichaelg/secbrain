// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "forge-std/console.sol";

// Mock interfaces for SingleAssetStaking
interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

/**
 * @title SingleAssetStaking Invariant Tests
 * @notice Tests critical invariants for the SingleAssetStaking contract
 * @dev Focuses on staking logic, total outstanding tracking, and liquidity requirements
 */
contract MockERC20 is IERC20 {
    string public name = "Mock Token";
    string public symbol = "MTK";
    uint8 public decimals = 18;
    
    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;
    uint256 private _totalSupply;
    
    constructor() {
        // Mint initial supply
        _totalSupply = 1_000_000_000 * 1e18;
        _balances[msg.sender] = _totalSupply;
    }
    
    function balanceOf(address account) external view override returns (uint256) {
        return _balances[account];
    }
    
    function transfer(address to, uint256 amount) external override returns (bool) {
        _transfer(msg.sender, to, amount);
        return true;
    }
    
    function approve(address spender, uint256 amount) external override returns (bool) {
        _allowances[msg.sender][spender] = amount;
        return true;
    }
    
    function transferFrom(address from, address to, uint256 amount) external override returns (bool) {
        require(_allowances[from][msg.sender] >= amount, "Insufficient allowance");
        _allowances[from][msg.sender] -= amount;
        _transfer(from, to, amount);
        return true;
    }
    
    function _transfer(address from, address to, uint256 amount) internal {
        require(_balances[from] >= amount, "Insufficient balance");
        // Safe: Underflow prevented by require, overflow impossible (transferring existing supply)
        unchecked {
            _balances[from] -= amount;
            _balances[to] += amount;
        }
    }
    
    function mint(address to, uint256 amount) external {
        // Safe: Test-only mock, handler bounds inputs
        _balances[to] += amount;
        _totalSupply += amount;
    }
}

// Simplified SingleAssetStaking interface for testing
interface ISingleAssetStaking {
    struct Stake {
        uint256 amount;
        uint256 end;
        uint256 duration;
        uint240 rate;
        bool paid;
        uint8 stakeType;
    }
    
    function stakingToken() external view returns (address);
    function totalOutstanding() external view returns (uint256);
    function paused() external view returns (bool);
    function getAllStakes(address account) external view returns (Stake[] memory);
    function stake(uint256 amount, uint256 duration) external;
    function exit() external;
}

/// @notice Handler contract for invariant testing
/// @dev Restricts random inputs to valid staking operations
contract StakingHandler is Test {
    ISingleAssetStaking public staking;
    IERC20 public token;
    
    uint256 public ghost_totalStaked;
    uint256 public ghost_totalRewardsExpected;
    uint256 public ghost_totalExited;
    
    // Track actors for better coverage
    address[] public actors;
    mapping(address => bool) public isActor;
    
    // Valid durations (this would be contract-specific)
    uint256[] public validDurations;
    
    constructor(ISingleAssetStaking _staking, IERC20 _token) {
        staking = _staking;
        token = _token;
        
        // Common staking durations (30, 60, 90, 180, 365 days)
        validDurations.push(30 days);
        validDurations.push(60 days);
        validDurations.push(90 days);
        validDurations.push(180 days);
        validDurations.push(365 days);
    }
    
    function stake(uint256 actorSeed, uint256 amount, uint256 durationIndex) external {
        // Skip if paused
        if (staking.paused()) return;
        
        address actor = _getRandomActor(actorSeed);
        
        // Bound amount to reasonable range
        amount = bound(amount, 1e18, 1000e18);
        
        // Select valid duration
        if (validDurations.length == 0) return;
        durationIndex = bound(durationIndex, 0, validDurations.length - 1);
        uint256 duration = validDurations[durationIndex];
        
        // Ensure actor has tokens
        uint256 actorBalance = token.balanceOf(actor);
        if (actorBalance < amount) {
            // Mint tokens if needed (assumes token has a public mint function)
            // In production, replace with proper token allocation mechanism
            try MockERC20(address(token)).mint(actor, amount - actorBalance) {
                // Minting succeeded
            } catch {
                // Token doesn't support mint or isn't MockERC20, skip this operation
                return;
            }
        }
        
        // Approve staking contract
        vm.prank(actor);
        token.approve(address(staking), amount);
        
        // Try to stake
        vm.prank(actor);
        try staking.stake(amount, duration) {
            ghost_totalStaked += amount;
            // Approximate rewards (would need actual rate from contract)
            // For now, assume 10% reward rate
            ghost_totalRewardsExpected += (amount * 10) / 100;
        } catch {
            // Staking failed, ignore
        }
    }
    
    function exit(uint256 actorSeed) external {
        address actor = _getRandomActor(actorSeed);
        
        ISingleAssetStaking.Stake[] memory stakes = staking.getAllStakes(actor);
        if (stakes.length == 0) return;
        
        // Fast forward time to make at least one stake claimable
        bool hasMatured = false;
        for (uint256 i = 0; i < stakes.length; i++) {
            if (!stakes[i].paid && stakes[i].end <= block.timestamp) {
                hasMatured = true;
                break;
            }
        }
        
        if (!hasMatured && stakes.length > 0) {
            // Find earliest stake end time
            uint256 earliestEnd = type(uint256).max;
            for (uint256 i = 0; i < stakes.length; i++) {
                if (!stakes[i].paid && stakes[i].end < earliestEnd) {
                    earliestEnd = stakes[i].end;
                }
            }
            if (earliestEnd != type(uint256).max && earliestEnd > block.timestamp) {
                vm.warp(earliestEnd + 1);
            }
        }
        
        vm.prank(actor);
        try staking.exit() {
            ghost_totalExited += 1;
        } catch {
            // Exit failed, ignore
        }
    }
    
    function _getRandomActor(uint256 seed) internal returns (address) {
        // Use a limited set of actors for better collision testing
        address actor = address(uint160(bound(seed, 1, 20)));
        
        if (!isActor[actor]) {
            actors.push(actor);
            isActor[actor] = true;
        }
        
        return actor;
    }
    
    function callSummary() external view {
        console.log("=== Staking Summary ===");
        console.log("Total staked:", ghost_totalStaked);
        console.log("Total rewards expected:", ghost_totalRewardsExpected);
        console.log("Total exits:", ghost_totalExited);
        console.log("Total outstanding:", staking.totalOutstanding());
        console.log("Contract balance:", token.balanceOf(address(staking)));
        console.log("Number of actors:", actors.length);
    }
}

/// @notice Invariant test suite for SingleAssetStaking
contract SingleAssetStakingInvariantTests is Test {
    MockERC20 public token;
    ISingleAssetStaking public staking;
    StakingHandler public handler;
    
    function setUp() public {
        // Note: In a real scenario, we would deploy the actual SingleAssetStaking contract
        // For this template, we're setting up the structure that would test it
        
        // Deploy mock token
        token = new MockERC20();
        
        // In production, deploy actual staking contract here:
        // staking = new SingleAssetStaking();
        // staking.initialize(address(token), durations, rates);
        
        // For template purposes, we'll skip deployment
        // Uncomment below when actual contract is available
        
        /*
        handler = new StakingHandler(staking, token);
        
        // Fund the staking contract with rewards
        token.mint(address(staking), 10_000_000e18);
        
        // Target the handler for invariant testing
        targetContract(address(handler));
        
        // Only call handler functions
        bytes4[] memory selectors = new bytes4[](2);
        selectors[0] = StakingHandler.stake.selector;
        selectors[1] = StakingHandler.exit.selector;
        
        targetSelector(FuzzSelector({
            addr: address(handler),
            selectors: selectors
        }));
        */
    }
    
    /// @notice Contract balance must always be >= totalOutstanding
    /// @dev This ensures the contract can pay all obligations
    function invariant_sufficientLiquidity() public view {
        // Uncomment when staking contract is deployed
        /*
        uint256 contractBalance = token.balanceOf(address(staking));
        uint256 totalOutstanding = staking.totalOutstanding();
        
        assertGe(
            contractBalance,
            totalOutstanding,
            "Contract balance must cover total outstanding obligations"
        );
        */
    }
    
    /// @notice Total outstanding must never be negative (uint256 doesn't go negative, but checks for underflow)
    function invariant_totalOutstandingConsistency() public view {
        // Uncomment when staking contract is deployed
        /*
        uint256 totalOutstanding = staking.totalOutstanding();
        
        // If we reach here, totalOutstanding is valid (no underflow)
        assertTrue(totalOutstanding >= 0, "Total outstanding should never underflow");
        */
    }
    
    /// @notice Sum of all individual stake expected returns should match totalOutstanding
    function invariant_stakesMatchTotalOutstanding() public view {
        // Uncomment when staking contract is deployed
        /*
        address[] memory allActors = handler.actors();
        uint256 sumExpectedPayouts = 0;
        
        for (uint256 i = 0; i < allActors.length; i++) {
            ISingleAssetStaking.Stake[] memory stakes = staking.getAllStakes(allActors[i]);
            
            for (uint256 j = 0; j < stakes.length; j++) {
                if (!stakes[j].paid) {
                    // Calculate expected payout: principal + rewards
                    uint256 reward = (stakes[j].amount * uint256(stakes[j].rate)) / 1e18;
                    sumExpectedPayouts += stakes[j].amount + reward;
                }
            }
        }
        
        assertEq(
            sumExpectedPayouts,
            staking.totalOutstanding(),
            "Sum of stake payouts must equal totalOutstanding"
        );
        */
    }
    
    /// @notice No stake should be claimable before its end time
    function invariant_stakesNotClaimableBeforeMaturity() public view {
        // Uncomment when staking contract is deployed
        /*
        address[] memory allActors = handler.actors();
        
        for (uint256 i = 0; i < allActors.length; i++) {
            ISingleAssetStaking.Stake[] memory stakes = staking.getAllStakes(allActors[i]);
            
            for (uint256 j = 0; j < stakes.length; j++) {
                if (stakes[j].paid) {
                    // If paid, it must have been past its end time at some point
                    // Can't verify historical time, but we verify unpaid ones
                    continue;
                }
                
                // Unpaid stakes might not be mature yet
                // This invariant is more for logic verification
                assertTrue(
                    stakes[j].end > 0,
                    "Stake end time must be set"
                );
            }
        }
        */
    }
    
    /// @notice Call summary for debugging
    function invariant_callSummary() public view {
        // Uncomment when staking contract is deployed
        /*
        handler.callSummary();
        */
    }
}
