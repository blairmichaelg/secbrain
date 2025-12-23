// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import {SingleAssetStaking} from "../../src/SingleAssetStaking_3675/contracts/staking/SingleAssetStaking.sol";
import {IERC20} from "../../src/SingleAssetStaking_3675/@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title Handler for SingleAssetStaking Invariant Tests
 * @notice Restricts random inputs to valid operations for invariant testing
 */
contract SingleAssetStakingHandler is Test {
    SingleAssetStaking public staking;
    MockERC20 public stakingToken;
    
    // Constants
    uint256 constant MAX_ACTORS = 10;
    
    // Ghost variables to track expected state
    uint256 public ghost_totalStaked;
    uint256 public ghost_totalRewards;
    uint256 public ghost_totalPaid;
    
    // Track actors for better coverage
    address[] public actors;
    mapping(address => bool) public isActor;
    
    // Track operations for debugging
    uint256 public callCount;
    
    constructor(SingleAssetStaking _staking, MockERC20 _token) {
        staking = _staking;
        stakingToken = _token;
    }
    
    function stake(uint256 actorSeed, uint256 amount, uint256 durationIndex) external {
        address actor = _getRandomActor(actorSeed);
        
        // Get available durations from the staking contract
        uint256[] memory durations = staking.getAllDurations();
        if (durations.length == 0) return;
        
        // Bound to valid duration index
        durationIndex = bound(durationIndex, 0, durations.length - 1);
        uint256 duration = durations[durationIndex];
        
        // Bound amount to reasonable values
        amount = bound(amount, 1e18, 1000e18);
        
        // Mint tokens to actor and approve
        stakingToken.mint(actor, amount);
        vm.prank(actor);
        stakingToken.approve(address(staking), amount);
        
        // Try to stake
        vm.prank(actor);
        try staking.stake(amount, duration) {
            ghost_totalStaked += amount;
            uint256[] memory rates = staking.getAllRates();
            uint256 reward = (amount * rates[durationIndex]) / 1e18;
            ghost_totalRewards += reward;
            callCount++;
        } catch {
            // Staking failed, no state change
        }
    }
    
    function exit(uint256 actorSeed) external {
        // Try to exit stakes for random actor
        if (actors.length == 0) return;
        
        uint256 actorIndex = bound(actorSeed, 0, actors.length - 1);
        address actor = actors[actorIndex];
        
        // Warp time forward to allow exits
        vm.warp(block.timestamp + 365 days);
        
        vm.prank(actor);
        try staking.exit() {
            // Track paid rewards
            callCount++;
        } catch {
            // Exit failed
        }
    }
    
    function _getRandomActor(uint256 seed) internal returns (address) {
        // Use a limited set of actors for better collision testing
        address actor = address(uint160(bound(seed, 1, MAX_ACTORS)));
        
        if (!isActor[actor]) {
            actors.push(actor);
            isActor[actor] = true;
        }
        
        return actor;
    }
    
    function callSummary() external view {
        console.log("Total calls:", callCount);
        console.log("Ghost total staked:", ghost_totalStaked);
        console.log("Ghost total rewards:", ghost_totalRewards);
        console.log("Contract totalOutstanding:", staking.totalOutstanding());
    }
}

/**
 * @title Mock ERC20 Token for Testing
 */
contract MockERC20 is Test {
    string public name = "Mock Token";
    string public symbol = "MOCK";
    uint8 public decimals = 18;
    
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    uint256 public totalSupply;
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    
    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
        totalSupply += amount;
        emit Transfer(address(0), to, amount);
    }
    
    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }
    
    function transfer(address to, uint256 amount) external returns (bool) {
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        emit Transfer(msg.sender, to, amount);
        return true;
    }
    
    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        require(balanceOf[from] >= amount, "Insufficient balance");
        require(allowance[from][msg.sender] >= amount, "Insufficient allowance");
        
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        allowance[from][msg.sender] -= amount;
        
        emit Transfer(from, to, amount);
        return true;
    }
}

/**
 * @title Invariant Tests for SingleAssetStaking
 * @notice Tests critical invariants that must hold under all conditions
 */
contract SingleAssetStakingInvariantTest is Test {
    SingleAssetStaking public staking;
    MockERC20 public stakingToken;
    SingleAssetStakingHandler public handler;
    
    address public governor = address(0x1337);
    
    function setUp() public {
        // Deploy mock token
        stakingToken = new MockERC20();
        
        // Deploy staking contract
        staking = new SingleAssetStaking();
        
        // Set up durations and rates
        uint256[] memory durations = new uint256[](3);
        durations[0] = 30 days;
        durations[1] = 90 days;
        durations[2] = 365 days;
        
        uint256[] memory rates = new uint256[](3);
        rates[0] = 0.05e18;  // 5%
        rates[1] = 0.15e18;  // 15%
        rates[2] = 0.50e18;  // 50%
        
        // Initialize staking contract
        vm.prank(governor);
        staking.initialize(address(stakingToken), durations, rates);
        
        // Fund staking contract with rewards
        stakingToken.mint(address(staking), 1000000e18);
        
        // Set up handler
        handler = new SingleAssetStakingHandler(staking, stakingToken);
        
        // Target the handler for invariant testing
        targetContract(address(handler));
        
        // Only call handler functions
        bytes4[] memory selectors = new bytes4[](2);
        selectors[0] = SingleAssetStakingHandler.stake.selector;
        selectors[1] = SingleAssetStakingHandler.exit.selector;
        
        targetSelector(FuzzSelector({
            addr: address(handler),
            selectors: selectors
        }));
    }
    
    /**
     * @notice Contract balance should always be >= totalOutstanding
     * @dev This ensures the contract can always pay out all stakes + rewards
     */
    function invariant_sufficientBalance() public view {
        uint256 contractBalance = stakingToken.balanceOf(address(staking));
        uint256 totalOut = staking.totalOutstanding();
        assertGe(contractBalance, totalOut, "Contract balance < totalOutstanding");
    }
    
    /**
     * @notice totalOutstanding should match expected accounting
     * @dev Verifies contract accounting is consistent with ghost state tracking
     */
    function invariant_totalOutstandingAccounting() public view {
        uint256 totalOut = staking.totalOutstanding();
        uint256 expectedTotalOut = handler.ghost_totalStaked() + handler.ghost_totalRewards();
        assertEq(totalOut, expectedTotalOut, "totalOutstanding accounting mismatch");
    }
    
    /**
     * @notice Staking should not be paused during normal operations
     * @dev Only governor should be able to pause
     */
    function invariant_notPausedByDefault() public view {
        assertFalse(staking.paused(), "Staking should not be paused");
    }
    
    /**
     * @notice Call summary for debugging
     */
    function invariant_callSummary() public view {
        handler.callSummary();
    }
}
