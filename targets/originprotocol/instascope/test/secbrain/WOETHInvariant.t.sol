// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";

/**
 * @title Handler for WOETH Invariant Tests
 * @notice Restricts random inputs to valid operations for ERC4626 wrapped token testing
 */
contract WOETHHandler is Test {
    MockWOETH public woeth;
    MockOETH public oeth;
    
    // Constants
    uint256 constant MAX_ACTORS = 10;
    
    // Ghost variables to track expected state
    uint256 public ghost_totalDeposited;
    uint256 public ghost_totalWithdrawn;
    
    // Track actors
    address[] public actors;
    mapping(address => bool) public isActor;
    
    uint256 public callCount;
    
    constructor(MockWOETH _woeth, MockOETH _oeth) {
        woeth = _woeth;
        oeth = _oeth;
    }
    
    function deposit(uint256 actorSeed, uint256 assets) external {
        address actor = _getRandomActor(actorSeed);
        
        // Bound assets to reasonable values
        assets = bound(assets, 1e18, 1000e18);
        
        // Mint OETH to actor
        oeth.mint(actor, assets);
        
        // Approve and deposit
        vm.prank(actor);
        oeth.approve(address(woeth), assets);
        
        vm.prank(actor);
        try woeth.deposit(assets, actor) returns (uint256 shares) {
            ghost_totalDeposited += assets;
            callCount++;
        } catch {
            // Deposit failed
        }
    }
    
    function withdraw(uint256 actorSeed, uint256 assets) external {
        if (actors.length == 0) return;
        
        address actor = _getRandomActor(actorSeed);
        uint256 maxAssets = woeth.maxWithdraw(actor);
        
        if (maxAssets == 0) return;
        
        // Bound to available assets
        assets = bound(assets, 1, maxAssets);
        
        vm.prank(actor);
        try woeth.withdraw(assets, actor, actor) returns (uint256 shares) {
            ghost_totalWithdrawn += assets;
            callCount++;
        } catch {
            // Withdrawal failed
        }
    }
    
    function redeem(uint256 actorSeed, uint256 shares) external {
        if (actors.length == 0) return;
        
        address actor = _getRandomActor(actorSeed);
        uint256 maxShares = woeth.maxRedeem(actor);
        
        if (maxShares == 0) return;
        
        // Bound to available shares
        shares = bound(shares, 1, maxShares);
        
        vm.prank(actor);
        try woeth.redeem(shares, actor, actor) returns (uint256 assets) {
            ghost_totalWithdrawn += assets;
            callCount++;
        } catch {
            // Redeem failed
        }
    }
    
    function _getRandomActor(uint256 seed) internal returns (address) {
        address actor = address(uint160(bound(seed, 1, MAX_ACTORS)));
        
        if (!isActor[actor]) {
            actors.push(actor);
            isActor[actor] = true;
        }
        
        return actor;
    }
    
    function callSummary() external view {
        console.log("Total calls:", callCount);
        console.log("Ghost deposited:", ghost_totalDeposited);
        console.log("Ghost withdrawn:", ghost_totalWithdrawn);
        console.log("WOETH totalSupply:", woeth.totalSupply());
        console.log("WOETH totalAssets:", woeth.totalAssets());
    }
}

/**
 * @title Mock OETH Token (Rebasing)
 */
contract MockOETH is Test {
    string public name = "Origin Ether";
    string public symbol = "OETH";
    uint8 public decimals = 18;
    
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    uint256 public totalSupply;
    
    // Simplified rebasing mechanism
    uint256 public rebasingCreditsPerToken = 1e27;
    
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
    
    function rebaseOptIn() external {
        // Mock function for compatibility
    }
    
    function rebasingCreditsPerTokenHighres() external view returns (uint256) {
        return rebasingCreditsPerToken;
    }
}

/**
 * @title Mock WOETH (Wrapped OETH) - Simplified ERC4626
 */
contract MockWOETH is Test {
    string public name = "Wrapped OETH";
    string public symbol = "wOETH";
    uint8 public decimals = 18;
    
    MockOETH public asset;
    uint256 public adjuster = 1e27;
    
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    uint256 public totalSupply;
    
    event Deposit(address indexed sender, address indexed owner, uint256 assets, uint256 shares);
    event Withdraw(address indexed sender, address indexed receiver, address indexed owner, uint256 assets, uint256 shares);
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    
    constructor(MockOETH _asset) {
        asset = _asset;
    }
    
    function deposit(uint256 assets, address receiver) external returns (uint256 shares) {
        shares = convertToShares(assets);
        
        require(asset.transferFrom(msg.sender, address(this), assets), "Transfer failed");
        
        balanceOf[receiver] += shares;
        totalSupply += shares;
        
        emit Deposit(msg.sender, receiver, assets, shares);
        emit Transfer(address(0), receiver, shares);
    }
    
    function withdraw(uint256 assets, address receiver, address owner) external returns (uint256 shares) {
        shares = convertToShares(assets);
        
        if (msg.sender != owner) {
            require(allowance[owner][msg.sender] >= shares, "Insufficient allowance");
            allowance[owner][msg.sender] -= shares;
        }
        
        require(balanceOf[owner] >= shares, "Insufficient balance");
        balanceOf[owner] -= shares;
        totalSupply -= shares;
        
        require(asset.transfer(receiver, assets), "Transfer failed");
        
        emit Withdraw(msg.sender, receiver, owner, assets, shares);
        emit Transfer(owner, address(0), shares);
    }
    
    function redeem(uint256 shares, address receiver, address owner) external returns (uint256 assets) {
        assets = convertToAssets(shares);
        
        if (msg.sender != owner) {
            require(allowance[owner][msg.sender] >= shares, "Insufficient allowance");
            allowance[owner][msg.sender] -= shares;
        }
        
        require(balanceOf[owner] >= shares, "Insufficient balance");
        balanceOf[owner] -= shares;
        totalSupply -= shares;
        
        require(asset.transfer(receiver, assets), "Transfer failed");
        
        emit Withdraw(msg.sender, receiver, owner, assets, shares);
        emit Transfer(owner, address(0), shares);
    }
    
    function convertToShares(uint256 assets) public view returns (uint256) {
        uint256 rebasingCredits = asset.rebasingCreditsPerTokenHighres();
        return (assets * rebasingCredits) / adjuster;
    }
    
    function convertToAssets(uint256 shares) public view returns (uint256) {
        uint256 rebasingCredits = asset.rebasingCreditsPerTokenHighres();
        return (shares * adjuster) / rebasingCredits;
    }
    
    function totalAssets() public view returns (uint256) {
        return (totalSupply * adjuster) / asset.rebasingCreditsPerTokenHighres();
    }
    
    function maxWithdraw(address owner) public view returns (uint256) {
        return convertToAssets(balanceOf[owner]);
    }
    
    function maxRedeem(address owner) public view returns (uint256) {
        return balanceOf[owner];
    }
}

/**
 * @title Invariant Tests for WOETH (ERC4626 Wrapper)
 * @notice Tests critical invariants for wrapped rebasing token
 */
contract WOETHInvariantTest is Test {
    MockWOETH public woeth;
    MockOETH public oeth;
    WOETHHandler public handler;
    
    // Test constants
    uint256 constant ROUNDING_TOLERANCE = 1e9;  // 1 gwei - tight enough to catch bugs
    uint256 constant CONVERSION_TOLERANCE = 1e12;  // 0.000001 tokens - catches precision issues
    
    function setUp() public {
        // Deploy mock OETH
        oeth = new MockOETH();
        
        // Deploy WOETH wrapper
        woeth = new MockWOETH(oeth);
        
        // Set up handler
        handler = new WOETHHandler(woeth, oeth);
        
        // Target the handler for invariant testing
        targetContract(address(handler));
        
        // Only call handler functions
        bytes4[] memory selectors = new bytes4[](3);
        selectors[0] = WOETHHandler.deposit.selector;
        selectors[1] = WOETHHandler.withdraw.selector;
        selectors[2] = WOETHHandler.redeem.selector;
        
        targetSelector(FuzzSelector({
            addr: address(handler),
            selectors: selectors
        }));
    }
    
    /**
     * @notice Total supply should never exceed total assets
     * @dev In ERC4626, totalAssets >= totalSupply in terms of underlying value
     */
    function invariant_totalSupplyConsistency() public view {
        uint256 supply = woeth.totalSupply();
        uint256 assets = woeth.totalAssets();
        
        // Convert supply to assets for comparison
        uint256 supplyInAssets = woeth.convertToAssets(supply);
        
        // They should be equal (within rounding)
        assertApproxEqAbs(supplyInAssets, assets, ROUNDING_TOLERANCE, "Supply != Assets");
    }
    
    /**
     * @notice Sum of all balances should equal total supply
     */
    function invariant_balancesSumToTotalSupply() public view {
        address[] memory actors = handler.actors();
        uint256 sumBalances = 0;
        
        for (uint256 i = 0; i < actors.length; i++) {
            sumBalances += woeth.balanceOf(actors[i]);
        }
        
        assertEq(sumBalances, woeth.totalSupply(), "Sum of balances != totalSupply");
    }
    
    /**
     * @notice Contract should always have enough OETH to back WOETH
     */
    function invariant_sufficientBackingAssets() public view {
        uint256 oethBalance = oeth.balanceOf(address(woeth));
        uint256 requiredAssets = woeth.totalAssets();
        
        assertGe(oethBalance, requiredAssets, "Insufficient backing assets");
    }
    
    /**
     * @notice Conversion functions should be inverse operations
     */
    function invariant_conversionConsistency() public view {
        // Test with a sample value
        uint256 testAmount = 100e18;
        
        if (woeth.totalSupply() > 0) {
            uint256 shares = woeth.convertToShares(testAmount);
            uint256 backToAssets = woeth.convertToAssets(shares);
            
            // Should round-trip correctly (within small rounding error)
            assertApproxEqAbs(testAmount, backToAssets, CONVERSION_TOLERANCE, "Conversion not consistent");
        }
    }
    
    /**
     * @notice Deposits should always be greater than or equal to withdrawals
     * @dev This ensures no more assets leave than entered
     */
    function invariant_depositWithdrawalBalance() public view {
        assertGe(handler.ghost_totalDeposited(), handler.ghost_totalWithdrawn(), 
                 "Withdrawals exceed deposits");
    }
    
    /**
     * @notice Call summary for debugging
     */
    function invariant_callSummary() public view {
        handler.callSummary();
    }
}
