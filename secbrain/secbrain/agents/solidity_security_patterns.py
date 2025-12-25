"""Advanced Solidity security patterns for vulnerability detection.

This module implements state-of-the-art smart contract security patterns
including reentrancy guards, flash loan attack detection, access control,
front-running protection, oracle security, and formal verification hints.

References:
- Consensys Smart Contract Best Practices
- Trail of Bits Building Secure Contracts
- DeFi Security Summit 2024 Findings
- Secureum Security Pitfalls
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class VulnerabilityPattern(Enum):
    """Advanced vulnerability patterns based on latest security research."""

    # Reentrancy patterns
    CLASSIC_REENTRANCY = "classic_reentrancy"
    CROSS_FUNCTION_REENTRANCY = "cross_function_reentrancy"
    READ_ONLY_REENTRANCY = "read_only_reentrancy"  # New attack vector (2023)
    CEI_VIOLATION = "checks_effects_interactions_violation"

    # Flash loan patterns
    FLASH_LOAN_PRICE_MANIPULATION = "flash_loan_price_manipulation"
    FLASH_LOAN_GOVERNANCE_ATTACK = "flash_loan_governance_attack"
    SAME_BLOCK_BORROW_REPAY = "same_block_borrow_repay"
    ORACLE_MANIPULATION_FLASH = "oracle_manipulation_flash"

    # Access control patterns
    MISSING_ACCESS_CONTROL = "missing_access_control"
    WEAK_ACCESS_CONTROL = "weak_access_control"
    ROLE_BASED_ACCESS_NEEDED = "role_based_access_needed"
    MULTI_LEVEL_ACCESS_MISSING = "multi_level_access_missing"

    # Front-running patterns
    FRONT_RUNNING_VULNERABLE = "front_running_vulnerable"
    MISSING_COMMIT_REVEAL = "missing_commit_reveal"
    NO_TIMELOCK = "no_timelock"
    MISSING_EIP712_SIGNATURE = "missing_eip712_signature"

    # Oracle security patterns
    STALE_PRICE_DATA = "stale_price_data"
    SINGLE_ORACLE_DEPENDENCY = "single_oracle_dependency"
    MISSING_TWAP = "missing_twap"
    NO_PRICE_DEVIATION_CHECK = "no_price_deviation_check"
    NO_MULTI_ORACLE_CONSENSUS = "no_multi_oracle_consensus"

    # Bridge security patterns (cross-chain)
    BRIDGE_MESSAGE_FORGERY = "bridge_message_forgery"
    MERKLE_PROOF_MANIPULATION = "merkle_proof_manipulation"
    SPV_PROOF_BYPASS = "spv_proof_bypass"
    CROSS_CHAIN_REPLAY = "cross_chain_replay"
    RELAY_CENSORSHIP = "relay_censorship"
    DEPOSIT_WITHDRAWAL_MISMATCH = "deposit_withdrawal_mismatch"
    BRIDGE_SIGNATURE_BYPASS = "bridge_signature_bypass"

    # DAO governance patterns
    GOVERNANCE_FLASH_LOAN_ATTACK = "governance_flash_loan_attack"
    PROPOSAL_EXECUTION_BYPASS = "proposal_execution_bypass"
    TIMELOCK_BYPASS = "timelock_bypass"
    QUORUM_MANIPULATION = "quorum_manipulation"
    DELEGATION_ATTACK = "delegation_attack"


@dataclass
class SecurityPattern:
    """Represents a security pattern with detection and mitigation."""

    pattern_type: VulnerabilityPattern
    severity: str  # "critical", "high", "medium", "low"
    description: str
    detection_heuristics: list[str] = field(default_factory=list)
    mitigation_code: str = ""
    references: list[str] = field(default_factory=list)


class SoliditySecurityPatterns:
    """Advanced Solidity security patterns database."""

    REENTRANCY_PATTERNS: dict[str, SecurityPattern] = {
        "classic_reentrancy": SecurityPattern(
            pattern_type=VulnerabilityPattern.CLASSIC_REENTRANCY,
            severity="critical",
            description="Classic reentrancy attack via external call before state update",
            detection_heuristics=[
                "external call",
                "state update after call",
                "balance transfer",
                "call.value",
                "transfer",
                "send",
            ],
            mitigation_code='''
// Use OpenZeppelin's ReentrancyGuard
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract Secure is ReentrancyGuard {
    function withdraw(uint256 amount) external nonReentrant {
        // Checks-Effects-Interactions pattern
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;  // Effect before interaction
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
    }
}
''',
            references=[
                "https://consensys.github.io/smart-contract-best-practices/attacks/reentrancy/",
            ],
        ),
        "read_only_reentrancy": SecurityPattern(
            pattern_type=VulnerabilityPattern.READ_ONLY_REENTRANCY,
            severity="high",
            description="Read-only reentrancy via view function calls during state changes (2023 attack vector)",
            detection_heuristics=[
                "view function",
                "external call in modifier",
                "getters during state change",
                "balanceof",
                "totalsupply",
            ],
            mitigation_code='''
// Protect view functions from read-only reentrancy
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract Secure is ReentrancyGuard {
    // Add nonReentrant to view functions that read critical state
    function getBalance(address user) external view nonReentrant returns (uint256) {
        return balances[user];
    }

    // Or use a reentrancy lock for all state-reading functions
    modifier nonReentrantView() {
        require(_status != _ENTERED, "ReentrancyGuard: reentrant call");
        _;
    }
}
''',
            references=[
                "https://github.com/pcaversaccio/reentrancy-attacks#read-only-reentrancy",
                "https://chainsecurity.com/curve-lp-oracle-manipulation-post-mortem/",
            ],
        ),
        "cei_violation": SecurityPattern(
            pattern_type=VulnerabilityPattern.CEI_VIOLATION,
            severity="high",
            description="Violation of Checks-Effects-Interactions pattern",
            detection_heuristics=[
                "interaction before effect",
                "call before state change",
                "transfer before update",
            ],
            mitigation_code='''
// Follow Checks-Effects-Interactions (CEI) pattern
function withdraw(uint256 amount) external {
    // 1. Checks
    require(balances[msg.sender] >= amount, "Insufficient balance");
    require(amount > 0, "Amount must be positive");

    // 2. Effects (update state BEFORE external calls)
    balances[msg.sender] -= amount;
    emit Withdrawal(msg.sender, amount);

    // 3. Interactions (external calls LAST)
    (bool success, ) = msg.sender.call{value: amount}("");
    require(success, "Transfer failed");
}
''',
            references=[
                "https://fravoll.github.io/solidity-patterns/checks_effects_interactions.html",
            ],
        ),
    }

    FLASH_LOAN_PATTERNS: dict[str, SecurityPattern] = {
        "flash_loan_price_manipulation": SecurityPattern(
            pattern_type=VulnerabilityPattern.FLASH_LOAN_PRICE_MANIPULATION,
            severity="critical",
            description="Flash loan attack to manipulate price oracles",
            detection_heuristics=[
                "flash loan",
                "price oracle",
                "spot price",
                "reserve manipulation",
                "liquidity check",
            ],
            mitigation_code='''
// Protect against flash loan price manipulation
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract Secure {
    AggregatorV3Interface internal priceFeed;
    uint256 constant MAX_PRICE_DEVIATION = 5; // 5% max deviation
    uint256 constant TWAP_PERIOD = 1800; // 30 minutes

    function getSecurePrice() public view returns (uint256) {
        // Use Chainlink oracle with staleness check
        (
            uint80 roundId,
            int256 price,
            ,
            uint256 updatedAt,
            uint80 answeredInRound
        ) = priceFeed.latestRoundData();

        require(price > 0, "Invalid price");
        require(answeredInRound >= roundId, "Stale price");
        require(block.timestamp - updatedAt < 3600, "Price too old");

        // Additional: Check price deviation
        uint256 twapPrice = getTWAP(TWAP_PERIOD);
        uint256 deviation = abs(uint256(price), twapPrice) * 100 / twapPrice;
        require(deviation <= MAX_PRICE_DEVIATION, "Price deviation too high");

        return uint256(price);
    }

    function getTWAP(uint256 period) internal view returns (uint256) {
        // Implement TWAP calculation
        // This prevents flash loan manipulation
    }
}
''',
            references=[
                "https://blog.chain.link/flash-loans-and-the-importance-of-tamper-proof-oracles/",
            ],
        ),
        "same_block_borrow_repay": SecurityPattern(
            pattern_type=VulnerabilityPattern.SAME_BLOCK_BORROW_REPAY,
            severity="high",
            description="Same-block borrow and repay detection for flash loan attacks",
            detection_heuristics=[
                "borrow",
                "repay",
                "block.number",
                "flashloan",
                "onflashloan",
            ],
            mitigation_code='''
// Detect and prevent same-block borrow/repay attacks
contract Secure {
    mapping(address => uint256) public lastBorrowBlock;
    mapping(address => uint256) public lastActionBlock;

    function borrow(uint256 amount) external {
        require(
            block.number > lastActionBlock[msg.sender],
            "Same block action prevented"
        );

        lastBorrowBlock[msg.sender] = block.number;
        lastActionBlock[msg.sender] = block.number;

        // Borrow logic...
    }

    function sensitiveAction() external {
        require(
            block.number > lastBorrowBlock[msg.sender],
            "Cannot act in same block as borrow"
        );

        lastActionBlock[msg.sender] = block.number;
        // Sensitive action logic...
    }
}
''',
            references=[
                "https://github.com/crytic/building-secure-contracts/tree/master/not-so-smart-contracts/flash_loan_attack",
            ],
        ),
    }

    ACCESS_CONTROL_PATTERNS: dict[str, SecurityPattern] = {
        "role_based_access": SecurityPattern(
            pattern_type=VulnerabilityPattern.ROLE_BASED_ACCESS_NEEDED,
            severity="high",
            description="Multi-level role-based access control needed instead of simple Ownable",
            detection_heuristics=[
                "onlyowner",
                "owner",
                "admin",
                "restricted function",
            ],
            mitigation_code='''
// Use OpenZeppelin's AccessControl for role-based permissions
import "@openzeppelin/contracts/access/AccessControl.sol";

contract Secure is AccessControl {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    function criticalOperation() external onlyRole(ADMIN_ROLE) {
        // Only admins can execute
    }

    function operatorAction() external onlyRole(OPERATOR_ROLE) {
        // Only operators can execute
    }

    function pause() external onlyRole(PAUSER_ROLE) {
        // Only pausers can execute
    }
}
''',
            references=[
                "https://docs.openzeppelin.com/contracts/4.x/access-control",
            ],
        ),
    }

    FRONT_RUNNING_PATTERNS: dict[str, SecurityPattern] = {
        "commit_reveal": SecurityPattern(
            pattern_type=VulnerabilityPattern.MISSING_COMMIT_REVEAL,
            severity="medium",
            description="Commit-reveal scheme needed to prevent front-running",
            detection_heuristics=[
                "commit",
                "bid",
                "auction",
                "vote",
                "random",
                "lottery",
                "commit",
                "reveal",
            ],
            mitigation_code='''
// Implement commit-reveal scheme
contract Secure {
    mapping(address => bytes32) public commitments;
    mapping(address => uint256) public revealDeadline;

    function commit(bytes32 commitment) external {
        require(commitments[msg.sender] == 0, "Already committed");
        commitments[msg.sender] = commitment;
        revealDeadline[msg.sender] = block.timestamp + 1 hours;
    }

    function reveal(uint256 value, bytes32 salt) external {
        require(commitments[msg.sender] != 0, "No commitment");
        require(block.timestamp <= revealDeadline[msg.sender], "Reveal deadline passed");

        bytes32 hash = keccak256(abi.encodePacked(msg.sender, value, salt));
        require(hash == commitments[msg.sender], "Invalid reveal");

        delete commitments[msg.sender];
        // Process revealed value...
    }
}
''',
            references=[
                "https://github.com/ethereumbook/ethereumbook/blob/develop/09smart-contracts-security.asciidoc#commit-and-reveal",
            ],
        ),
        "eip712_signature": SecurityPattern(
            pattern_type=VulnerabilityPattern.MISSING_EIP712_SIGNATURE,
            severity="medium",
            description="EIP-712 typed data signatures for protection against signature replay",
            detection_heuristics=[
                "signature",
                "ecrecover",
                "permit",
                "meta-transaction",
            ],
            mitigation_code='''
// Use EIP-712 for signed messages
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";

contract Secure is EIP712 {
    bytes32 public constant PERMIT_TYPEHASH =
        keccak256("Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)");

    mapping(address => uint256) public nonces;

    constructor() EIP712("SecureToken", "1") {}

    function permit(
        address owner,
        address spender,
        uint256 value,
        uint256 deadline,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        require(block.timestamp <= deadline, "Signature expired");

        bytes32 structHash = keccak256(
            abi.encode(PERMIT_TYPEHASH, owner, spender, value, nonces[owner]++, deadline)
        );

        bytes32 hash = _hashTypedDataV4(structHash);
        address signer = ECDSA.recover(hash, v, r, s);
        require(signer == owner, "Invalid signature");

        // Process permit...
    }
}
''',
            references=[
                "https://eips.ethereum.org/EIPS/eip-712",
            ],
        ),
    }

    ORACLE_SECURITY_PATTERNS: dict[str, SecurityPattern] = {
        "chainlink_staleness": SecurityPattern(
            pattern_type=VulnerabilityPattern.STALE_PRICE_DATA,
            severity="high",
            description="Chainlink price feed staleness checks required",
            detection_heuristics=[
                "latestrounddata",
                "chainlink",
                "price feed",
                "oracle",
            ],
            mitigation_code='''
// Implement Chainlink staleness checks
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract Secure {
    AggregatorV3Interface internal priceFeed;
    uint256 public constant STALENESS_THRESHOLD = 3600; // 1 hour

    function getLatestPrice() public view returns (uint256) {
        (
            uint80 roundId,
            int256 price,
            ,
            uint256 updatedAt,
            uint80 answeredInRound
        ) = priceFeed.latestRoundData();

        // Check for stale data
        require(answeredInRound >= roundId, "Stale price: round not complete");
        require(block.timestamp - updatedAt <= STALENESS_THRESHOLD, "Stale price: too old");
        require(price > 0, "Invalid price: must be positive");

        return uint256(price);
    }
}
''',
            references=[
                "https://docs.chain.link/data-feeds/historical-data",
            ],
        ),
        "multi_oracle_consensus": SecurityPattern(
            pattern_type=VulnerabilityPattern.NO_MULTI_ORACLE_CONSENSUS,
            severity="medium",
            description="Multi-oracle consensus for critical price data",
            detection_heuristics=[
                "single oracle",
                "price feed",
                "critical price",
            ],
            mitigation_code='''
// Implement multi-oracle consensus
contract Secure {
    AggregatorV3Interface[] public priceFeeds;
    uint256 public constant MAX_PRICE_DEVIATION = 3; // 3%

    function getConsensusPrice() public view returns (uint256) {
        require(priceFeeds.length >= 3, "Need at least 3 oracles");

        uint256[] memory prices = new uint256[](priceFeeds.length);

        // Collect prices from all oracles
        for (uint256 i = 0; i < priceFeeds.length; i++) {
            (, int256 price, , uint256 updatedAt, ) = priceFeeds[i].latestRoundData();
            require(price > 0, "Invalid price");
            require(block.timestamp - updatedAt < 3600, "Stale price");
            prices[i] = uint256(price);
        }

        // Calculate median price
        uint256 medianPrice = _median(prices);

        // Verify all prices are within acceptable deviation
        for (uint256 i = 0; i < prices.length; i++) {
            uint256 deviation = abs(prices[i], medianPrice) * 100 / medianPrice;
            require(deviation <= MAX_PRICE_DEVIATION, "Price deviation too high");
        }

        return medianPrice;
    }

    function _median(uint256[] memory values) internal pure returns (uint256) {
        // Sort and return median
        _quickSort(values, 0, int256(values.length - 1));
        return values[values.length / 2];
    }
}
''',
            references=[
                "https://blog.chain.link/decentralized-oracle-networks/",
            ],
        ),
        "twap_implementation": SecurityPattern(
            pattern_type=VulnerabilityPattern.MISSING_TWAP,
            severity="medium",
            description="Time-Weighted Average Price (TWAP) implementation for manipulation resistance",
            detection_heuristics=[
                "spot price",
                "instant price",
                "uniswap price",
            ],
            mitigation_code='''
// Implement TWAP oracle
import "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import "@uniswap/v3-periphery/contracts/libraries/OracleLibrary.sol";

contract Secure {
    IUniswapV3Pool public pool;
    uint32 public constant TWAP_PERIOD = 1800; // 30 minutes

    function getTWAP() public view returns (uint256) {
        uint32[] memory secondsAgos = new uint32[](2);
        secondsAgos[0] = TWAP_PERIOD;
        secondsAgos[1] = 0;

        (int56[] memory tickCumulatives, ) = pool.observe(secondsAgos);

        int56 tickCumulativesDelta = tickCumulatives[1] - tickCumulatives[0];
        int24 arithmeticMeanTick = int24(tickCumulativesDelta / int56(uint56(TWAP_PERIOD)));

        uint256 quoteAmount = OracleLibrary.getQuoteAtTick(
            arithmeticMeanTick,
            uint128(1e18),
            address(token0),
            address(token1)
        );

        return quoteAmount;
    }
}
''',
            references=[
                "https://docs.uniswap.org/contracts/v3/guides/advanced/price-oracle",
            ],
        ),
    }

    BRIDGE_SECURITY_PATTERNS: dict[str, SecurityPattern] = {
        "bridge_message_forgery": SecurityPattern(
            pattern_type=VulnerabilityPattern.BRIDGE_MESSAGE_FORGERY,
            severity="critical",
            description="Cross-chain message forgery allowing unauthorized operations",
            detection_heuristics=[
                "cross-chain",
                "message",
                "relay",
                "bridge",
                "verify message",
                "relayer",
            ],
            mitigation_code='''
// Secure cross-chain message verification
contract SecureBridge {
    mapping(bytes32 => bool) public processedMessages;
    mapping(address => bool) public trustedRelayers;
    
    event MessageProcessed(bytes32 indexed messageHash);
    
    function processMessage(
        bytes memory message,
        bytes[] memory signatures,
        uint256 nonce
    ) external {
        // Prevent replay attacks
        bytes32 messageHash = keccak256(abi.encodePacked(message, nonce, block.chainid));
        require(!processedMessages[messageHash], "Message already processed");
        
        // Verify signatures from trusted relayers
        require(signatures.length >= 3, "Need at least 3 signatures");
        
        address[] memory signers = new address[](signatures.length);
        mapping(address => bool) seenSigners;
        for (uint256 i = 0; i < signatures.length; i++) {
            address signer = ECDSA.recover(messageHash, signatures[i]);
            require(trustedRelayers[signer], "Invalid signer");
            
            // Prevent duplicate signers with O(1) lookup
            require(!seenSigners[signer], "Duplicate signer");
            seenSigners[signer] = true;
            signers[i] = signer;
        }
        
        processedMessages[messageHash] = true;
        emit MessageProcessed(messageHash);
        
        // Process message...
    }
}
''',
            references=[
                "https://github.com/nomad-xyz/nomad-monorepo/blob/main/packages/contracts-core/contracts/Replica.sol",
            ],
        ),
        "merkle_proof_verification": SecurityPattern(
            pattern_type=VulnerabilityPattern.MERKLE_PROOF_MANIPULATION,
            severity="critical",
            description="Merkle proof verification vulnerabilities in bridges",
            detection_heuristics=[
                "merkle",
                "proof",
                "verify",
                "root",
                "leaf",
            ],
            mitigation_code='''
// Secure Merkle proof verification
import "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";

contract SecureBridge {
    bytes32 public merkleRoot;
    mapping(bytes32 => bool) public claimedLeaves;
    
    function claimWithProof(
        bytes32 leaf,
        bytes32[] calldata proof
    ) external {
        // Prevent double-claiming
        require(!claimedLeaves[leaf], "Already claimed");
        
        // Verify proof
        require(
            MerkleProof.verify(proof, merkleRoot, leaf),
            "Invalid Merkle proof"
        );
        
        claimedLeaves[leaf] = true;
        
        // Process claim...
    }
    
    // Admin function with timelock
    function updateMerkleRoot(bytes32 newRoot) external onlyRole(ADMIN_ROLE) {
        require(newRoot != bytes32(0), "Invalid root");
        merkleRoot = newRoot;
    }
}
''',
            references=[
                "https://docs.openzeppelin.com/contracts/4.x/api/utils#MerkleProof",
            ],
        ),
        "spv_proof_verification": SecurityPattern(
            pattern_type=VulnerabilityPattern.SPV_PROOF_BYPASS,
            severity="critical",
            description="Bitcoin SPV proof verification bypass in tBTC-style bridges",
            detection_heuristics=[
                "spv",
                "bitcoin",
                "btc",
                "proof",
                "transaction proof",
                "header",
            ],
            mitigation_code='''
// Secure Bitcoin SPV proof verification (tBTC-style)
contract SecureBitcoinBridge {
    uint256 public constant MIN_CONFIRMATIONS = 6;
    uint256 public constant DIFFICULTY_ADJUSTMENT_INTERVAL = 2016;
    
    mapping(bytes32 => bool) public verifiedTransactions;
    
    function verifyTransaction(
        bytes memory txBytes,
        bytes memory merkleProof,
        bytes memory blockHeader,
        uint256 blockHeight
    ) external {
        // Extract transaction hash
        bytes32 txHash = sha256(abi.encodePacked(sha256(txBytes)));
        require(!verifiedTransactions[txHash], "Transaction already verified");
        
        // Verify Merkle proof
        bytes32 merkleRoot = extractMerkleRoot(blockHeader);
        require(verifyMerkleProof(txHash, merkleProof, merkleRoot), "Invalid Merkle proof");
        
        // Verify block header
        require(verifyBlockHeader(blockHeader, blockHeight), "Invalid block header");
        
        // Require minimum confirmations
        require(
            getCurrentBlockHeight() >= blockHeight + MIN_CONFIRMATIONS,
            "Insufficient confirmations"
        );
        
        verifiedTransactions[txHash] = true;
        
        // Process verified transaction...
    }
    
    function verifyBlockHeader(bytes memory header, uint256 height) internal view returns (bool) {
        // Verify proof of work
        bytes32 headerHash = sha256(abi.encodePacked(sha256(header)));
        uint256 target = extractTarget(header);
        require(uint256(headerHash) < target, "Invalid proof of work");
        
        // Additional checks: difficulty adjustment, timestamp, etc.
        return true;
    }
}
''',
            references=[
                "https://docs.threshold.network/applications/tbtc-v2/tbtc-v2-technical-design",
            ],
        ),
        "cross_chain_replay_protection": SecurityPattern(
            pattern_type=VulnerabilityPattern.CROSS_CHAIN_REPLAY,
            severity="high",
            description="Cross-chain replay attack protection",
            detection_heuristics=[
                "chain id",
                "nonce",
                "replay",
                "cross-chain",
            ],
            mitigation_code='''
// Prevent cross-chain replay attacks
contract SecureBridge {
    mapping(bytes32 => bool) public processedMessages;
    uint256 public nonce;
    
    function processMessage(
        bytes memory message,
        uint256 messageNonce,
        uint256 sourceChainId,
        bytes memory signature
    ) external {
        // Include chain IDs in message hash
        bytes32 messageHash = keccak256(
            abi.encodePacked(
                message,
                messageNonce,
                sourceChainId,
                block.chainid,  // Destination chain ID
                address(this)   // Contract address
            )
        );
        
        require(!processedMessages[messageHash], "Message already processed");
        require(messageNonce == nonce + 1, "Invalid nonce");
        
        // Verify signature
        address signer = ECDSA.recover(messageHash, signature);
        require(trustedRelayer[signer], "Unauthorized signer");
        
        processedMessages[messageHash] = true;
        nonce = messageNonce;
        
        // Process message...
    }
}
''',
            references=[
                "https://eips.ethereum.org/EIPS/eip-155",
            ],
        ),
    }

    DAO_GOVERNANCE_PATTERNS: dict[str, SecurityPattern] = {
        "governance_flash_loan": SecurityPattern(
            pattern_type=VulnerabilityPattern.GOVERNANCE_FLASH_LOAN_ATTACK,
            severity="critical",
            description="Flash loan attack to temporarily gain voting power for malicious proposals",
            detection_heuristics=[
                "governance",
                "vote",
                "proposal",
                "voting power",
                "delegate",
                "flash loan vulnerable",
            ],
            mitigation_code='''
// Protect governance from flash loan attacks
import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";

contract SecureGovernor is Governor, GovernorVotes {
    uint256 public constant VOTING_DELAY = 1 days;  // Delay before voting starts
    uint256 public constant VOTING_PERIOD = 3 days;  // Voting duration
    
    constructor(IVotes _token) Governor("SecureDAO") GovernorVotes(_token) {}
    
    function votingDelay() public pure override returns (uint256) {
        return VOTING_DELAY;  // Prevents flash loan attacks
    }
    
    function votingPeriod() public pure override returns (uint256) {
        return VOTING_PERIOD;
    }
    
    // Use snapshot-based voting (voting power at proposal creation)
    function _getVotes(
        address account,
        uint256 blockNumber,
        bytes memory /*params*/
    ) internal view override returns (uint256) {
        return token.getPastVotes(account, blockNumber);
    }
}
''',
            references=[
                "https://blog.openzeppelin.com/protect-your-users-with-smart-contract-timelocks",
            ],
        ),
        "timelock_protection": SecurityPattern(
            pattern_type=VulnerabilityPattern.TIMELOCK_BYPASS,
            severity="high",
            description="Timelock bypass allowing immediate execution of critical operations",
            detection_heuristics=[
                "timelock",
                "delay",
                "execute",
                "queue",
                "governance",
            ],
            mitigation_code='''
// Implement secure timelock for governance
import "@openzeppelin/contracts/governance/TimelockController.sol";

contract SecureDAO {
    TimelockController public timelock;
    uint256 public constant MIN_DELAY = 2 days;
    
    constructor(address[] memory proposers, address[] memory executors) {
        timelock = new TimelockController(
            MIN_DELAY,
            proposers,
            executors,
            address(this)  // Admin (can change roles)
        );
    }
    
    function executeProposal(
        address target,
        uint256 value,
        bytes calldata data,
        bytes32 predecessor,
        bytes32 salt
    ) external {
        // Must be scheduled first with MIN_DELAY
        timelock.execute(target, value, data, predecessor, salt);
    }
    
    function scheduleProposal(
        address target,
        uint256 value,
        bytes calldata data,
        bytes32 predecessor,
        bytes32 salt,
        uint256 delay
    ) external onlyRole(PROPOSER_ROLE) {
        require(delay >= MIN_DELAY, "Delay too short");
        timelock.schedule(target, value, data, predecessor, salt, delay);
    }
}
''',
            references=[
                "https://docs.openzeppelin.com/contracts/4.x/api/governance#TimelockController",
            ],
        ),
        "quorum_protection": SecurityPattern(
            pattern_type=VulnerabilityPattern.QUORUM_MANIPULATION,
            severity="high",
            description="Quorum manipulation through supply changes or voting power concentration",
            detection_heuristics=[
                "quorum",
                "voting threshold",
                "minimum votes",
                "total supply",
            ],
            mitigation_code='''
// Secure quorum implementation
import "@openzeppelin/contracts/governance/Governor.sol";

contract SecureGovernor is Governor {
    uint256 public constant QUORUM_PERCENTAGE = 4;  // 4% of total supply
    uint256 public constant MIN_QUORUM_VOTES = 1_000_000e18;  // Minimum absolute quorum
    
    function quorum(uint256 blockNumber) public view override returns (uint256) {
        uint256 totalSupply = token.getPastTotalSupply(blockNumber);
        uint256 percentageQuorum = (totalSupply * QUORUM_PERCENTAGE) / 100;
        
        // Use the higher of percentage-based or absolute minimum
        return percentageQuorum > MIN_QUORUM_VOTES ? percentageQuorum : MIN_QUORUM_VOTES;
    }
    
    // Additional: Prevent quorum manipulation via supply changes
    function propose(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        string memory description
    ) public override returns (uint256) {
        // Check proposer has minimum voting power
        uint256 proposerVotes = getVotes(msg.sender, block.number - 1);
        require(
            proposerVotes >= proposalThreshold(),
            "Proposer votes below threshold"
        );
        
        return super.propose(targets, values, calldatas, description);
    }
}
''',
            references=[
                "https://docs.openzeppelin.com/contracts/4.x/governance",
            ],
        ),
        "delegation_safety": SecurityPattern(
            pattern_type=VulnerabilityPattern.DELEGATION_ATTACK,
            severity="medium",
            description="Delegation attack allowing unauthorized voting power transfer",
            detection_heuristics=[
                "delegate",
                "delegatebysig",
                "voting power",
                "transfer votes",
            ],
            mitigation_code='''
// Secure delegation implementation
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";

contract SecureGovernanceToken is ERC20Votes {
    // Minimum delegation period before votes become active
    uint256 public constant DELEGATION_DELAY = 1 days;
    
    mapping(address => uint256) public delegationTimestamp;
    
    constructor() ERC20("SecureDAO", "SDAO") ERC20Permit("SecureDAO") {}
    
    function delegate(address delegatee) public override {
        super.delegate(delegatee);
        delegationTimestamp[msg.sender] = block.timestamp;
    }
    
    function delegateBySig(
        address delegatee,
        uint256 nonce,
        uint256 expiry,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) public override {
        super.delegateBySig(delegatee, nonce, expiry, v, r, s);
        delegationTimestamp[_msgSender()] = block.timestamp;
    }
    
    // Override to enforce delegation delay
    function _getVotes(
        address account,
        uint256 blockNumber,
        bytes memory params
    ) internal view override returns (uint256) {
        // Only enforce the delegation delay for current block queries.
        // Historical snapshots cannot reliably enforce a time-based delay using the current timestamp.
        if (blockNumber == block.number) {
            if (block.timestamp < delegationTimestamp[account] + DELEGATION_DELAY) {
                return 0;  // Votes not active yet
            }
        }
        return super._getVotes(account, blockNumber, params);
    }
}
''',
            references=[
                "https://docs.openzeppelin.com/contracts/4.x/api/token/erc20#ERC20Votes",
            ],
        ),
    }

    @classmethod
    def get_all_patterns(cls) -> dict[str, SecurityPattern]:
        """Get all security patterns."""
        all_patterns = {}
        all_patterns.update(cls.REENTRANCY_PATTERNS)
        all_patterns.update(cls.FLASH_LOAN_PATTERNS)
        all_patterns.update(cls.ACCESS_CONTROL_PATTERNS)
        all_patterns.update(cls.FRONT_RUNNING_PATTERNS)
        all_patterns.update(cls.ORACLE_SECURITY_PATTERNS)
        all_patterns.update(cls.BRIDGE_SECURITY_PATTERNS)
        all_patterns.update(cls.DAO_GOVERNANCE_PATTERNS)
        return all_patterns

    @classmethod
    def detect_patterns(cls, contract_code: str, abi: list[Any]) -> list[SecurityPattern]:
        """Detect security patterns in contract code."""
        detected = []
        all_patterns = cls.get_all_patterns()

        code_lower = contract_code.lower()

        for _pattern_key, pattern in all_patterns.items():
            # Check if any detection heuristics match
            for heuristic in pattern.detection_heuristics:
                if heuristic.lower() in code_lower:
                    detected.append(pattern)
                    break

        return detected

    @classmethod
    def get_mitigation_for_pattern(cls, pattern_type: VulnerabilityPattern) -> str:
        """Get mitigation code for a specific pattern."""
        all_patterns = cls.get_all_patterns()

        for pattern in all_patterns.values():
            if pattern.pattern_type == pattern_type:
                return pattern.mitigation_code

        return ""


class FormalVerificationPatterns:
    """Formal verification hints and patterns for invariant testing."""

    @staticmethod
    def generate_natspec_invariants(function_name: str, invariants: list[str]) -> str:
        """Generate NatSpec annotations for invariants."""
        invariant_docs = "\n".join([f"    /// @invariant {inv}" for inv in invariants])

        return f'''
    /// @notice {function_name}
{invariant_docs}
    /// @dev Ensure all invariants hold before and after execution
'''

    @staticmethod
    def generate_foundry_invariant_test(contract_name: str, invariants: list[str]) -> str:
        """Generate Foundry invariant test template."""
        invariant_checks = "\n        ".join([
            f"assertTrue({inv}, \"Invariant failed: {inv}\");"
            for inv in invariants
        ])

        return f'''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "../src/{contract_name}.sol";

contract {contract_name}InvariantTest is Test {{
    {contract_name} public target;

    function setUp() public {{
        target = new {contract_name}();
    }}

    /// @dev Foundry will call this after every function call
    function invariant_criticalInvariants() public {{
        {invariant_checks}
    }}
}}
'''

    @staticmethod
    def get_common_invariants() -> dict[str, list[str]]:
        """Get common invariants for different contract types."""
        return {
            "erc20": [
                "totalSupply == sum(balanceOf(user) for all users)",
                "balanceOf(user) <= totalSupply for all users",
                "balanceOf(user) >= 0 for all users",
            ],
            "vault": [
                "totalAssets >= sum(userDeposits)",
                "sharePrice never decreases (except for losses)",
                "totalShares * sharePrice == totalAssets",
            ],
            "lending": [
                "totalBorrowed <= totalDeposited",
                "userCollateral >= userBorrowedValue * collateralRatio",
                "sum(userDeposits) >= sum(userBorrows)",
            ],
            "staking": [
                "totalStaked == sum(userStakes)",
                "rewardsDistributed <= rewardsAllocated",
                "userRewards >= 0",
            ],
        }
