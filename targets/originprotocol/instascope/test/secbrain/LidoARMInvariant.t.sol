// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import "forge-std/Test.sol";

/**
 * @title Handler for LidoARM Invariant Tests
 * @notice Restricts random inputs to valid operations for ARM testing
 * @dev Simplified handler for testing basic ARM invariants
 */
contract LidoARMHandler is Test {
    MockLidoARM public arm;
    MockERC20 public weth;
    MockERC20 public steth;
    
    // Constants
    uint256 constant MAX_ACTORS = 10;
    
    // Ghost variables
    uint256 public ghost_totalDeposits;
    uint256 public ghost_totalSwaps;
    
    // Track actors
    address[] public actors;
    mapping(address => bool) public isActor;
    
    uint256 public callCount;
    
    constructor(MockLidoARM _arm, MockERC20 _weth, MockERC20 _steth) {
        arm = _arm;
        weth = _weth;
        steth = _steth;
    }
    
    function deposit(uint256 actorSeed, uint256 assets) external {
        address actor = _getRandomActor(actorSeed);
        
        // Bound assets to reasonable values
        assets = bound(assets, 1e18, 1000e18);
        
        // Mint WETH to actor
        weth.mint(actor, assets);
        
        // Approve and deposit
        vm.prank(actor);
        weth.approve(address(arm), assets);
        
        vm.prank(actor);
        try arm.deposit(assets, actor) returns (uint256 shares) {
            ghost_totalDeposits += assets;
            callCount++;
        } catch {
            // Deposit failed
        }
    }
    
    function swapExactTokensForTokens(uint256 actorSeed, uint256 amountIn, bool wethToSteth) external {
        address actor = _getRandomActor(actorSeed);
        
        // Bound amount
        amountIn = bound(amountIn, 1e17, 100e18);
        
        if (wethToSteth) {
            // Swap WETH for stETH
            weth.mint(actor, amountIn);
            vm.prank(actor);
            weth.approve(address(arm), amountIn);
        } else {
            // Swap stETH for WETH
            steth.mint(actor, amountIn);
            vm.prank(actor);
            steth.approve(address(arm), amountIn);
        }
        
        vm.prank(actor);
        try arm.swapExactTokensForTokens(
            wethToSteth ? address(weth) : address(steth),
            wethToSteth ? address(steth) : address(weth),
            amountIn,
            0,
            actor
        ) returns (uint256 amountOut) {
            ghost_totalSwaps += amountIn;
            callCount++;
        } catch {
            // Swap failed
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
        console.log("Ghost deposits:", ghost_totalDeposits);
        console.log("Ghost swaps:", ghost_totalSwaps);
        console.log("ARM totalSupply:", arm.totalSupply());
        console.log("ARM totalAssets:", arm.totalAssets());
    }
}

/**
 * @title Mock ERC20 Token
 */
contract MockERC20 is Test {
    string public name;
    string public symbol;
    uint8 public decimals = 18;
    
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    uint256 public totalSupply;
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    
    constructor(string memory _name, string memory _symbol) {
        name = _name;
        symbol = _symbol;
    }
    
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
 * @title Mock LidoARM - Simplified Automated Redemption Manager
 */
contract MockLidoARM is Test {
    MockERC20 public weth;
    MockERC20 public steth;
    
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    uint256 public totalSupply;
    
    // Swap prices (simplified)
    uint256 public wethToStethPrice = 1e18;  // 1:1
    uint256 public stethToWethPrice = 0.99e18;  // 0.99:1 (small discount)
    
    event Deposit(address indexed sender, address indexed owner, uint256 assets, uint256 shares);
    event Swap(address indexed sender, address tokenIn, address tokenOut, uint256 amountIn, uint256 amountOut);
    event Transfer(address indexed from, address indexed to, uint256 value);
    
    constructor(MockERC20 _weth, MockERC20 _steth) {
        weth = _weth;
        steth = _steth;
    }
    
    function deposit(uint256 assets, address receiver) external returns (uint256 shares) {
        // 1:1 share:asset ratio for simplicity
        shares = assets;
        
        require(weth.transferFrom(msg.sender, address(this), assets), "Transfer failed");
        
        balanceOf[receiver] += shares;
        totalSupply += shares;
        
        emit Deposit(msg.sender, receiver, assets, shares);
        emit Transfer(address(0), receiver, shares);
    }
    
    function swapExactTokensForTokens(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 minAmountOut,
        address to
    ) external returns (uint256 amountOut) {
        require(tokenIn == address(weth) || tokenIn == address(steth), "Invalid token in");
        require(tokenOut == address(weth) || tokenOut == address(steth), "Invalid token out");
        require(tokenIn != tokenOut, "Same tokens");
        
        MockERC20 tokenInContract = MockERC20(tokenIn);
        MockERC20 tokenOutContract = MockERC20(tokenOut);
        
        // Calculate output amount based on price
        if (tokenIn == address(weth)) {
            amountOut = (amountIn * wethToStethPrice) / 1e18;
        } else {
            amountOut = (amountIn * stethToWethPrice) / 1e18;
        }
        
        require(amountOut >= minAmountOut, "Insufficient output");
        
        // Transfer tokens
        require(tokenInContract.transferFrom(msg.sender, address(this), amountIn), "Transfer in failed");
        require(tokenOutContract.transfer(to, amountOut), "Transfer out failed");
        
        emit Swap(msg.sender, tokenIn, tokenOut, amountIn, amountOut);
    }
    
    function totalAssets() public view returns (uint256) {
        return weth.balanceOf(address(this));
    }
}

/**
 * @title Invariant Tests for LidoARM
 * @notice Tests critical invariants for the Automated Redemption Manager
 */
contract LidoARMInvariantTest is Test {
    MockLidoARM public arm;
    MockERC20 public weth;
    MockERC20 public steth;
    LidoARMHandler public handler;
    
    function setUp() public {
        // Deploy mock tokens
        weth = new MockERC20("Wrapped Ether", "WETH");
        steth = new MockERC20("Staked Ether", "stETH");
        
        // Deploy ARM
        arm = new MockLidoARM(weth, steth);
        
        // Fund ARM with initial liquidity
        weth.mint(address(arm), 10000e18);
        steth.mint(address(arm), 10000e18);
        
        // Set up handler
        handler = new LidoARMHandler(arm, weth, steth);
        
        // Target the handler for invariant testing
        targetContract(address(handler));
        
        // Only call handler functions
        bytes4[] memory selectors = new bytes4[](2);
        selectors[0] = LidoARMHandler.deposit.selector;
        selectors[1] = LidoARMHandler.swapExactTokensForTokens.selector;
        
        targetSelector(FuzzSelector({
            addr: address(handler),
            selectors: selectors
        }));
    }
    
    /**
     * @notice ARM should maintain sufficient liquidity
     * @dev Combined WETH + stETH balance should be above minimum threshold
     */
    function invariant_sufficientLiquidity() public view {
        uint256 wethBalance = weth.balanceOf(address(arm));
        uint256 stethBalance = steth.balanceOf(address(arm));
        
        // Should have meaningful liquidity (at least 1 token) in at least one asset
        uint256 minLiquidity = 1e18;
        assertTrue(wethBalance >= minLiquidity || stethBalance >= minLiquidity, 
                   "Insufficient liquidity for swaps");
    }
    
    /**
     * @notice Total supply should track total assets deposited
     * @dev For simplified 1:1 share ratio, verify bidirectional relationship
     */
    function invariant_sharesToAssetsConsistency() public view {
        uint256 supply = arm.totalSupply();
        uint256 assets = arm.totalAssets();
        
        // Bidirectional relationship: if shares exist, assets must exist, and vice versa
        if (supply > 0) {
            assertTrue(assets > 0, "Assets should exist if shares exist");
        }
        
        // Additionally, assets should not exist without corresponding shares
        if (assets > 0) {
            assertTrue(supply > 0, "Shares should exist if assets exist");
        }
    }
    
    /**
     * @notice Sum of balances equals total supply
     */
    function invariant_balancesSumToTotalSupply() public view {
        address[] memory actors = handler.actors();
        uint256 sumBalances = 0;
        
        for (uint256 i = 0; i < actors.length; i++) {
            sumBalances += arm.balanceOf(actors[i]);
        }
        
        assertEq(sumBalances, arm.totalSupply(), "Sum of balances != totalSupply");
    }
    
    /**
     * @notice Call summary for debugging
     */
    function invariant_callSummary() public view {
        handler.callSummary();
    }
}
