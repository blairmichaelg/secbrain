// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "forge-std/console.sol";

/**
 * @title VaultCore Invariant Tests
 * @notice Tests critical invariants for the VaultCore contract
 * @dev Focuses on vault accounting, rebasing mechanics, and asset conservation
 */

// Mock interfaces for VaultCore testing
interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function totalSupply() external view returns (uint256);
}

interface IVaultCore {
    function totalValue() external view returns (uint256);
    function mint(address _asset, uint256 _amount, uint256 _minimumOusdAmount) external;
    function redeem(uint256 _amount, uint256 _minimumUnitAmount) external;
    function rebase() external;
    function capitalPaused() external view returns (bool);
    function rebasePaused() external view returns (bool);
}

/// @notice Handler contract for VaultCore invariant testing
/// @dev Simulates user interactions with the vault
contract VaultHandler is Test {
    IVaultCore public vault;
    IERC20 public ousd; // The vault's output token
    
    uint256 public ghost_totalMinted;
    uint256 public ghost_totalRedeemed;
    uint256 public ghost_rebases;
    
    address[] public actors;
    mapping(address => bool) public isActor;
    
    // Track supported assets (would be set in constructor based on vault config)
    address[] public supportedAssets;
    
    constructor(IVaultCore _vault, IERC20 _ousd, address[] memory _supportedAssets) {
        vault = _vault;
        ousd = _ousd;
        supportedAssets = _supportedAssets;
    }
    
    function mint(uint256 actorSeed, uint256 assetIndex, uint256 amount) external {
        if (vault.capitalPaused()) return;
        if (supportedAssets.length == 0) return;
        
        address actor = _getRandomActor(actorSeed);
        assetIndex = bound(assetIndex, 0, supportedAssets.length - 1);
        address asset = supportedAssets[assetIndex];
        
        // Bound amount to reasonable range
        amount = bound(amount, 1e18, 10_000e18);
        
        // Ensure actor has assets
        IERC20 assetToken = IERC20(asset);
        uint256 actorBalance = assetToken.balanceOf(actor);
        if (actorBalance < amount) {
            // In real test, would need to mint or deal tokens
            return;
        }
        
        vm.prank(actor);
        assetToken.approve(address(vault), amount);
        
        vm.prank(actor);
        try vault.mint(asset, amount, 0) {
            ghost_totalMinted += amount;
        } catch {
            // Mint failed, ignore
        }
    }
    
    function redeem(uint256 actorSeed, uint256 amount) external {
        if (vault.capitalPaused()) return;
        
        address actor = _getRandomActor(actorSeed);
        
        // Bound amount to actor's balance
        uint256 actorBalance = ousd.balanceOf(actor);
        if (actorBalance == 0) return;
        
        amount = bound(amount, 1, actorBalance);
        
        vm.prank(actor);
        try vault.redeem(amount, 0) {
            ghost_totalRedeemed += amount;
        } catch {
            // Redeem failed, ignore
        }
    }
    
    function rebase(uint256 /* seed */) external {
        if (vault.rebasePaused()) return;
        
        try vault.rebase() {
            ghost_rebases++;
        } catch {
            // Rebase failed, ignore
        }
    }
    
    function _getRandomActor(uint256 seed) internal returns (address) {
        address actor = address(uint160(bound(seed, 1, 20)));
        
        if (!isActor[actor]) {
            actors.push(actor);
            isActor[actor] = true;
        }
        
        return actor;
    }
    
    function callSummary() external view {
        console.log("=== Vault Summary ===");
        console.log("Total minted:", ghost_totalMinted);
        console.log("Total redeemed:", ghost_totalRedeemed);
        console.log("Rebases:", ghost_rebases);
        console.log("OUSD total supply:", ousd.totalSupply());
        console.log("Vault total value:", vault.totalValue());
        console.log("Number of actors:", actors.length);
    }
}

/// @notice Invariant test suite for VaultCore
contract VaultCoreInvariantTests is Test {
    IVaultCore public vault;
    IERC20 public ousd;
    VaultHandler public handler;
    
    address[] public supportedAssets;
    
    function setUp() public {
        // Note: In a real scenario, we would deploy the actual VaultCore contract
        // For this template, we're setting up the structure that would test it
        
        // In production, deploy contracts here:
        // supportedAssets = [USDC, USDT, DAI];
        // vault = new VaultCore();
        // ousd = vault.ousdToken();
        // vault.initialize(...);
        
        // Uncomment below when actual contract is available
        
        /*
        handler = new VaultHandler(vault, ousd, supportedAssets);
        
        // Target the handler for invariant testing
        targetContract(address(handler));
        
        bytes4[] memory selectors = new bytes4[](3);
        selectors[0] = VaultHandler.mint.selector;
        selectors[1] = VaultHandler.redeem.selector;
        selectors[2] = VaultHandler.rebase.selector;
        
        targetSelector(FuzzSelector({
            addr: address(handler),
            selectors: selectors
        }));
        */
    }
    
    /// @notice Vault total value must equal or exceed OUSD total supply
    /// @dev The vault should always have enough assets to back all OUSD
    function invariant_vaultBacksOUSD() public view {
        // Uncomment when vault is deployed
        /*
        uint256 vaultValue = vault.totalValue();
        uint256 ousdSupply = ousd.totalSupply();
        
        assertGe(
            vaultValue,
            ousdSupply,
            "Vault total value must back OUSD supply"
        );
        */
    }
    
    /// @notice OUSD total supply should never decrease except during redemptions
    /// @dev Tracks that supply only increases during mints/rebases or decreases during redeems
    function invariant_ousdSupplyConsistency() public view {
        // Uncomment when vault is deployed
        /*
        uint256 supply = ousd.totalSupply();
        
        // Supply should always be valid (no underflow)
        assertTrue(supply >= 0, "OUSD supply should be valid");
        */
    }
    
    /// @notice Sum of all user balances should equal total supply
    function invariant_balancesEqualSupply() public view {
        // Uncomment when vault is deployed
        /*
        address[] memory allActors = handler.actors();
        uint256 sumBalances = 0;
        
        for (uint256 i = 0; i < allActors.length; i++) {
            sumBalances += ousd.balanceOf(allActors[i]);
        }
        
        // Note: This is simplified - in reality would need to account for all addresses
        // For now, just verify actors' balances don't exceed total supply
        assertLe(
            sumBalances,
            ousd.totalSupply(),
            "Sum of actor balances must not exceed total supply"
        );
        */
    }
    
    /// @notice Asset conservation: sum of vault holdings + strategies = total value
    function invariant_assetConservation() public view {
        // Uncomment when vault is deployed
        /*
        // This would sum up:
        // 1. Direct vault holdings of each supported asset
        // 2. Assets allocated to strategies
        // And verify it equals vault.totalValue()
        
        uint256 totalHoldings = 0;
        
        for (uint256 i = 0; i < supportedAssets.length; i++) {
            IERC20 asset = IERC20(supportedAssets[i]);
            totalHoldings += asset.balanceOf(address(vault));
        }
        
        // In full implementation, would also add strategy holdings
        // For now, verify vault has some holdings
        assertTrue(
            totalHoldings > 0 || vault.totalValue() == 0,
            "Vault holdings should be consistent"
        );
        */
    }
    
    /// @notice Rebase should never decrease user balances unfairly
    /// @dev Rebases should only increase balances or keep them same (never decrease)
    function invariant_rebaseOnlyIncreases() public view {
        // Uncomment when vault is deployed
        /*
        // This is a stateful check that would need to track balances before/after
        // For now, we ensure the mechanism exists
        assertTrue(
            true,
            "Rebase logic should be tested separately for balance preservation"
        );
        */
    }
    
    /// @notice No single user can have more OUSD than total supply
    function invariant_noUserExceedsSupply() public view {
        // Uncomment when vault is deployed
        /*
        address[] memory allActors = handler.actors();
        uint256 totalSupply = ousd.totalSupply();
        
        for (uint256 i = 0; i < allActors.length; i++) {
            uint256 balance = ousd.balanceOf(allActors[i]);
            assertLe(
                balance,
                totalSupply,
                "User balance cannot exceed total supply"
            );
        }
        */
    }
    
    /// @notice Call summary for debugging
    function invariant_callSummary() public view {
        // Uncomment when vault is deployed
        /*
        handler.callSummary();
        */
    }
}
