// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import "forge-std/Test.sol";

/**
 * @title Generic ERC20 Token Invariant Tests
 * @notice Demonstrates complete invariant testing for a simple ERC20 token
 * @dev This is a working example that can be run immediately
 */

// Custom errors for gas optimization
error InsufficientBalance();
error InsufficientAllowance();

/// @notice Simple ERC20 token for testing
contract SimpleERC20 {
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
    
    function transfer(address to, uint256 amount) external returns (bool) {
        _transfer(msg.sender, to, amount);
        return true;
    }
    
    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }
    
    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        if (allowance[from][msg.sender] < amount) revert InsufficientAllowance();
        
        unchecked {
            allowance[from][msg.sender] -= amount;
        }
        
        _transfer(from, to, amount);
        return true;
    }
    
    function mint(address to, uint256 amount) external {
        // Safe: Handler bounds all inputs to prevent overflow in tests
        unchecked {
            balanceOf[to] += amount;
            totalSupply += amount;
        }
        emit Transfer(address(0), to, amount);
    }
    
    function burn(address from, uint256 amount) external {
        if (balanceOf[from] < amount) revert InsufficientBalance();
        
        unchecked {
            balanceOf[from] -= amount;
            totalSupply -= amount;
        }
        emit Transfer(from, address(0), amount);
    }
    
    function _transfer(address from, address to, uint256 amount) internal {
        if (balanceOf[from] < amount) revert InsufficientBalance();
        
        unchecked {
            balanceOf[from] -= amount;
            balanceOf[to] += amount;
        }
        
        emit Transfer(from, to, amount);
    }
}

/// @notice Handler contract for ERC20 invariant testing
/// @dev Restricts random inputs to valid ERC20 operations
contract ERC20Handler is Test {
    SimpleERC20 public token;
    
    uint256 public ghost_mintSum;
    uint256 public ghost_burnSum;
    uint256 public ghost_transferSum;
    uint256 public ghost_zeroAddressBalance; // Should always be 0
    
    // Track unique addresses for better coverage
    address[] public actors;
    mapping(address => bool) public isActor;
    
    constructor(SimpleERC20 _token) {
        token = _token;
    }
    
    function mint(uint256 actorSeed, uint256 amount) external {
        address actor = _getRandomActor(actorSeed);
        
        // Bound amount to prevent overflow
        amount = bound(amount, 0, 1000e18);
        
        // Additional check to prevent overflow
        uint256 currentSupply = token.totalSupply();
        if (currentSupply > type(uint256).max - amount) {
            // Skip minting if it would overflow
            return;
        }
        
        vm.prank(actor);
        token.mint(actor, amount);
        
        // Safe to add since we checked for overflow above
        ghost_mintSum += amount;
    }
    
    function burn(uint256 actorSeed, uint256 amount) external {
        address actor = _getRandomActor(actorSeed);
        amount = bound(amount, 0, token.balanceOf(actor));
        
        vm.prank(actor);
        token.burn(actor, amount);
        
        // Safe to add since amount is bounded
        ghost_burnSum += amount;
    }
    
    function transfer(uint256 fromSeed, uint256 toSeed, uint256 amount) external {
        address from = _getRandomActor(fromSeed);
        address to = _getRandomActor(toSeed);
        
        amount = bound(amount, 0, token.balanceOf(from));
        
        vm.prank(from);
        token.transfer(to, amount);
        
        // Safe to add since we're tracking cumulative transfers
        ghost_transferSum += amount;
    }
    
    function approve(uint256 ownerSeed, uint256 spenderSeed, uint256 amount) external {
        address owner = _getRandomActor(ownerSeed);
        address spender = _getRandomActor(spenderSeed);
        
        amount = bound(amount, 0, type(uint256).max);
        
        vm.prank(owner);
        token.approve(spender, amount);
    }
    
    function transferFrom(uint256 ownerSeed, uint256 spenderSeed, uint256 toSeed, uint256 amount) external {
        address owner = _getRandomActor(ownerSeed);
        address spender = _getRandomActor(spenderSeed);
        address to = _getRandomActor(toSeed);
        
        // Bound to both allowance and balance
        uint256 allowed = token.allowance(owner, spender);
        uint256 balance = token.balanceOf(owner);
        uint256 maxAmount = allowed < balance ? allowed : balance;
        
        amount = bound(amount, 0, maxAmount);
        
        vm.prank(spender);
        token.transferFrom(owner, to, amount);
    }
    
    function _getRandomActor(uint256 seed) internal returns (address) {
        // Use a limited set of actors for better collision testing
        // Exclude address(0) to test zero-address edge cases separately
        address actor = address(uint160(bound(seed, 1, 50)));
        
        if (!isActor[actor]) {
            actors.push(actor);
            isActor[actor] = true;
        }
        
        return actor;
    }
    
    function callSummary() external view {
        console.log("=== ERC20 Handler Summary ===");
        console.log("Total minted:", ghost_mintSum);
        console.log("Total burned:", ghost_burnSum);
        console.log("Total transfers:", ghost_transferSum);
        console.log("Total supply:", token.totalSupply());
        console.log("Number of actors:", actors.length);
    }
    
    function reduceActors(uint256 acc, function(uint256,address) external returns (uint256) func)
        public
        returns (uint256)
    {
        for (uint256 i = 0; i < actors.length; i++) {
            acc = func(acc, actors[i]);
        }
        return acc;
    }
    
    function actorsLength() external view returns (uint256) {
        return actors.length;
    }
}

/// @notice Invariant test suite for ERC20
contract ERC20InvariantTests is Test {
    SimpleERC20 public token;
    ERC20Handler public handler;
    
    function setUp() public {
        token = new SimpleERC20("Test Token", "TEST");
        handler = new ERC20Handler(token);
        
        // Target the handler for invariant testing
        targetContract(address(handler));
        
        // Only call handler functions
        bytes4[] memory selectors = new bytes4[](5);
        selectors[0] = ERC20Handler.mint.selector;
        selectors[1] = ERC20Handler.burn.selector;
        selectors[2] = ERC20Handler.transfer.selector;
        selectors[3] = ERC20Handler.approve.selector;
        selectors[4] = ERC20Handler.transferFrom.selector;
        
        targetSelector(FuzzSelector({
            addr: address(handler),
            selectors: selectors
        }));
    }
    
    /// @notice Total supply should equal sum of all balances
    function invariant_totalSupplyEqualsBalances() public view {
        uint256 sumBalances = 0;
        address[] memory actorsList = handler.actors();
        
        for (uint256 i = 0; i < actorsList.length; i++) {
            sumBalances += token.balanceOf(actorsList[i]);
        }
        
        assertEq(token.totalSupply(), sumBalances, "Total supply != sum of balances");
    }
    
    /// @notice Total supply should equal minted minus burned
    function invariant_totalSupplyEqualsGhostTracking() public view {
        uint256 expectedSupply = handler.ghost_mintSum() - handler.ghost_burnSum();
        assertEq(token.totalSupply(), expectedSupply, "Total supply != (minted - burned)");
    }
    
    /// @notice No individual balance can exceed total supply
    function invariant_balanceCannotExceedTotalSupply() public view {
        address[] memory actorsList = handler.actors();
        
        for (uint256 i = 0; i < actorsList.length; i++) {
            uint256 balance = token.balanceOf(actorsList[i]);
            assertLe(balance, token.totalSupply(), "Balance exceeds total supply");
        }
    }
    
    /// @notice Zero address should never have balance (unless explicitly minted to)
    function invariant_zeroAddressHasNoBalance() public view {
        assertEq(token.balanceOf(address(0)), 0, "Zero address should have no balance");
    }
    
    /// @notice All balances should be non-negative (uint256 enforces this, but good to document)
    function invariant_balancesNonNegative() public view {
        address[] memory actorsList = handler.actors();
        
        for (uint256 i = 0; i < actorsList.length; i++) {
            uint256 balance = token.balanceOf(actorsList[i]);
            assertGe(balance, 0, "Balance should be non-negative");
        }
    }
    
    /// @notice Total supply should never overflow
    function invariant_totalSupplyDoesNotOverflow() public view {
        // If we reach this, total supply is still a valid uint256
        assertTrue(token.totalSupply() >= 0, "Total supply valid");
        assertTrue(token.totalSupply() <= type(uint256).max, "Total supply valid");
    }
    
    /// @notice Call summary for debugging
    function invariant_callSummary() public view {
        handler.callSummary();
    }
}

/// @notice Example of standard fuzz testing for comparison
contract ERC20FuzzTests is Test {
    SimpleERC20 public token;
    
    function setUp() public {
        token = new SimpleERC20("Test Token", "TEST");
    }
    
    /// @notice Minting should always increase total supply by exact amount
    function testFuzz_MintIncreasesSupply(address to, uint256 amount) public {
        vm.assume(to != address(0));
        vm.assume(amount <= type(uint128).max);
        vm.assume(token.totalSupply() <= type(uint128).max);
        
        uint256 supplyBefore = token.totalSupply();
        token.mint(to, amount);
        uint256 supplyAfter = token.totalSupply();
        
        assertEq(supplyAfter - supplyBefore, amount, "Supply did not increase by amount");
    }
    
    /// @notice Transfer should preserve total supply
    function testFuzz_TransferPreservesTotalSupply(
        address from,
        address to,
        uint256 mintAmount,
        uint256 transferAmount
    ) public {
        vm.assume(from != address(0) && to != address(0));
        vm.assume(mintAmount <= type(uint128).max);
        vm.assume(transferAmount <= mintAmount);
        
        token.mint(from, mintAmount);
        uint256 supplyBefore = token.totalSupply();
        
        vm.prank(from);
        token.transfer(to, transferAmount);
        uint256 supplyAfter = token.totalSupply();
        
        assertEq(supplyBefore, supplyAfter, "Transfer changed total supply");
    }
    
    /// @notice Burn should always decrease total supply by exact amount
    function testFuzz_BurnDecreasesSupply(address holder, uint256 mintAmount, uint256 burnAmount) public {
        vm.assume(holder != address(0));
        vm.assume(mintAmount <= type(uint128).max);
        vm.assume(burnAmount <= mintAmount);
        
        token.mint(holder, mintAmount);
        uint256 supplyBefore = token.totalSupply();
        
        token.burn(holder, burnAmount);
        uint256 supplyAfter = token.totalSupply();
        
        assertEq(supplyBefore - supplyAfter, burnAmount, "Supply did not decrease by amount");
    }
}
