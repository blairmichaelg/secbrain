"""Advanced research agent for cutting-edge vulnerability discovery.

This module provides advanced research capabilities including:
- Novel vulnerability pattern discovery using AI
- Zero-day vulnerability hypothesis generation
- Cross-protocol vulnerability correlation
- Emerging attack vector identification
- Deep code pattern analysis
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from secbrain.core.context import RunContext
    from secbrain.tools.perplexity_research import PerplexityResearch

logger = logging.getLogger(__name__)


@dataclass
class ResearchFinding:
    """A research finding from advanced analysis."""

    title: str
    description: str
    severity: str  # critical, high, medium, low
    confidence: float  # 0.0 to 1.0
    research_source: str
    attack_vectors: list[str] = field(default_factory=list)
    affected_patterns: list[str] = field(default_factory=list)
    mitigation: str = ""
    references: list[str] = field(default_factory=list)
    exploit_complexity: str = "medium"  # low, medium, high

    def to_hypothesis(self) -> dict[str, Any]:
        """Convert finding to vulnerability hypothesis format."""
        return {
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "confidence": self.confidence,
            "attack_vectors": self.attack_vectors,
            "affected_patterns": self.affected_patterns,
            "mitigation": self.mitigation,
            "exploit_complexity": self.exploit_complexity,
        }


class AdvancedResearchAgent:
    """
    Agent for advanced vulnerability research and discovery.

    Capabilities:
    - Analyzes cutting-edge research papers and disclosures
    - Identifies emerging vulnerability patterns
    - Correlates findings across multiple protocols
    - Generates novel vulnerability hypotheses
    - Tracks zero-day indicators
    """

    def __init__(
        self,
        run_context: RunContext,
        research_client: PerplexityResearch | None = None,
    ):
        self.run_context = run_context
        self.research_client = research_client
        self.findings: list[ResearchFinding] = []

    async def research_emerging_patterns(
        self,
        timeframe_days: int = 90,
    ) -> list[ResearchFinding]:
        """
        Research emerging vulnerability patterns from recent exploits.

        Args:
            timeframe_days: How many days back to look for patterns

        Returns:
            List of research findings about emerging patterns
        """
        logger.info(f"Researching emerging patterns from last {timeframe_days} days")

        # Query for recent high-impact vulnerabilities
        query = f"""
        What are the most critical smart contract vulnerabilities discovered in the last {timeframe_days} days?
        Focus on:
        1. Zero-day exploits in DeFi protocols
        2. Novel attack vectors not widely known
        3. Vulnerabilities with public exploits or PoCs
        4. Cross-chain or bridge-related issues
        5. Account abstraction and intent-based protocol issues

        For each vulnerability, provide:
        - Attack vector and technique
        - Affected protocols
        - Exploit complexity
        - Mitigation strategies
        """

        findings = []

        if self.research_client:
            try:
                result = await self.research_client.research(
                    question=query,
                    context="Security research for bug bounty hunting",
                    ttl_hours=24,  # Cache for 24 hours
                )

                # Parse research result into findings
                # This is simplified - real implementation would use LLM to structure data
                findings.append(ResearchFinding(
                    title="Emerging Vulnerability Patterns",
                    description=result.get("answer", ""),
                    severity="high",
                    confidence=0.75,
                    research_source="perplexity",
                    references=result.get("sources", []),
                ))

                logger.info(f"Found {len(findings)} emerging patterns")
            except Exception:
                logger.exception("Research failed")
        else:
            # Dry-run or no client - return curated findings
            findings.extend(self._get_curated_emerging_patterns())

        self.findings.extend(findings)
        return findings

    def _get_curated_emerging_patterns(self) -> list[ResearchFinding]:
        """Get curated list of emerging vulnerability patterns (2024-2025)."""
        return [
            ResearchFinding(
                title="Intent-Based Protocol Atomicity Failures",
                description=(
                    "Intent-based protocols (UniswapX, CoW Protocol, 1inch Fusion) are vulnerable to "
                    "atomicity failures where solver/filler transactions can be manipulated to extract "
                    "value. Key issues include partial fills without proper slippage protection, "
                    "cross-domain MEV extraction, and solver collusion attacks."
                ),
                severity="critical",
                confidence=0.85,
                research_source="curated",
                attack_vectors=[
                    "Partial fill manipulation",
                    "Solver sandwich attacks",
                    "Cross-domain MEV extraction",
                    "Intent signature replay",
                ],
                affected_patterns=[
                    "Intent settlement without atomicity guarantees",
                    "Missing solver reputation checks",
                    "Insufficient slippage protection in intents",
                ],
                mitigation=(
                    "Implement atomic settlement with strong guarantees, add solver reputation systems, "
                    "enforce strict slippage bounds, use commit-reveal schemes for intent execution."
                ),
                references=[
                    "https://www.paradigm.xyz/2023/06/intents",
                    "https://collective.flashbots.net/t/rfp-12-mev-in-intent-architectures/2150",
                ],
                exploit_complexity="medium",
            ),
            ResearchFinding(
                title="ERC-4337 Paymaster Exploitation",
                description=(
                    "Account abstraction implementations using ERC-4337 are vulnerable through paymaster "
                    "contracts. Attackers can abuse gas sponsorship mechanisms, manipulate UserOperation "
                    "validation, or exploit bundler selection logic to drain paymaster funds or grief "
                    "legitimate users."
                ),
                severity="high",
                confidence=0.80,
                research_source="curated",
                attack_vectors=[
                    "Paymaster gas sponsorship abuse",
                    "UserOperation validation bypass",
                    "Bundler manipulation",
                    "Signature aggregation attacks",
                ],
                affected_patterns=[
                    "Uncapped gas sponsorship in paymasters",
                    "Missing UserOp validation checks",
                    "Bundler centralization vulnerabilities",
                ],
                mitigation=(
                    "Implement strict gas limits in paymasters, add comprehensive UserOp validation, "
                    "use decentralized bundler networks, implement rate limiting and reputation systems."
                ),
                references=[
                    "https://eips.ethereum.org/EIPS/eip-4337",
                    "https://www.alchemy.com/blog/account-abstraction",
                ],
                exploit_complexity="high",
            ),
            ResearchFinding(
                title="ZK-Proof Verification Circuit Flaws",
                description=(
                    "Zero-knowledge proof systems (ZK-SNARKs, ZK-STARKs) in L2s and privacy protocols "
                    "can have subtle circuit implementation bugs allowing proof forgery or verification "
                    "bypass. These include constraint system underconstraining, trusted setup exploitation, "
                    "and polynomial commitment scheme attacks."
                ),
                severity="critical",
                confidence=0.70,
                research_source="curated",
                attack_vectors=[
                    "Constraint system underconstraining",
                    "Trusted setup parameter manipulation",
                    "Polynomial commitment forgery",
                    "Witness manipulation",
                ],
                affected_patterns=[
                    "Underconstrained circuit implementations",
                    "Missing range checks in circuits",
                    "Weak trusted setup ceremonies",
                ],
                mitigation=(
                    "Conduct formal verification of circuits, use multi-party trusted setups, "
                    "implement comprehensive constraint testing, audit polynomial commitment schemes."
                ),
                references=[
                    "https://0xparc.org/blog/zk-bug-tracker",
                    "https://blog.trailofbits.com/2022/04/18/the-frozen-heart-vulnerability-in-circom/",
                ],
                exploit_complexity="high",
            ),
            ResearchFinding(
                title="Read-Only Reentrancy in View Functions",
                description=(
                    "View/pure functions can be exploited during reentrancy to read stale state data, "
                    "particularly in LP token pricing, oracle queries, and balance checks. This enables "
                    "attacks on protocols that assume view functions are safe from reentrancy."
                ),
                severity="critical",
                confidence=0.90,
                research_source="curated",
                attack_vectors=[
                    "View function call during reentrancy callback",
                    "Stale oracle price exploitation",
                    "LP token valuation manipulation",
                    "Balance snapshot attacks",
                ],
                affected_patterns=[
                    "Unguarded view functions in DeFi protocols",
                    "Oracle price queries without reentrancy protection",
                    "LP token pricing during callbacks",
                ],
                mitigation=(
                    "Add reentrancy guards to view functions, use Checks-Effects-Interactions pattern, "
                    "implement state consistency checks, avoid external calls before state updates."
                ),
                references=[
                    "https://chainsecurity.com/curve-lp-oracle-manipulation-post-mortem/",
                    "https://blog.pessimistic.io/read-only-reentrancy-in-depth-6ea7e9d78e85",
                ],
                exploit_complexity="medium",
            ),
            ResearchFinding(
                title="Optimistic Bridge Challenge Period Bypass",
                description=(
                    "Optimistic bridges (Optimism, Arbitrum, Base) rely on challenge periods for fraud "
                    "proofs. Vulnerabilities include challenge period manipulation, proposer centralization "
                    "risks, and state root forgery when validators are offline or censored."
                ),
                severity="critical",
                confidence=0.75,
                research_source="curated",
                attack_vectors=[
                    "Challenge period manipulation",
                    "Validator censorship attacks",
                    "State root forgery",
                    "Fraud proof suppression",
                ],
                affected_patterns=[
                    "Single sequencer dependency",
                    "Insufficient validator decentralization",
                    "Weak challenge mechanisms",
                ],
                mitigation=(
                    "Decentralize sequencer/proposer roles, implement multiple validator systems, "
                    "add economic incentives for challenging, use time-locked withdrawals."
                ),
                references=[
                    "https://l2beat.com/scaling/risk",
                    "https://medium.com/ethereum-optimism/optimisms-decentralization-roadmap-bb9b9c0e5c18",
                ],
                exploit_complexity="high",
            ),
            ResearchFinding(
                title="Concentrated Liquidity MEV Extraction",
                description=(
                    "Concentrated liquidity AMMs (Uniswap V3, Curve V2) enable sophisticated MEV attacks "
                    "through tick manipulation, liquidity position front-running, and JIT (Just-In-Time) "
                    "liquidity attacks that extract value from swappers."
                ),
                severity="high",
                confidence=0.85,
                research_source="curated",
                attack_vectors=[
                    "Tick manipulation around swaps",
                    "JIT liquidity sandwich attacks",
                    "Position front-running",
                    "Fee tier gaming",
                ],
                affected_patterns=[
                    "Predictable swap routing",
                    "Public mempool exposure",
                    "Lack of MEV protection",
                ],
                mitigation=(
                    "Use private mempools (Flashbots Protect), implement MEV-resistant designs, "
                    "add slippage protection, consider batch auctions or time-weighted pricing."
                ),
                references=[
                    "https://arxiv.org/abs/2106.00667",
                    "https://writings.flashbots.net/",
                ],
                exploit_complexity="medium",
            ),
        ]

    async def analyze_protocol_specific(
        self,
        protocol_name: str,
        blockchain: str = "Ethereum",
    ) -> list[ResearchFinding]:
        """
        Conduct protocol-specific vulnerability research.

        Args:
            protocol_name: Name of the protocol to research
            blockchain: Blockchain the protocol runs on

        Returns:
            List of protocol-specific findings
        """
        logger.info(f"Analyzing {protocol_name} on {blockchain}")

        query = f"""
        Analyze security vulnerabilities specific to {protocol_name} on {blockchain}.
        Focus on:
        1. Known historical vulnerabilities and fixes
        2. Protocol-specific attack surfaces
        3. Integration risks with other protocols
        4. Unique features that could be exploited
        5. Similar protocols that have been exploited

        Provide specific attack vectors and exploitation techniques.
        """

        findings = []

        if self.research_client:
            try:
                result = await self.research_client.research(
                    question=query,
                    context=f"Deep security analysis of {protocol_name}",
                    ttl_hours=48,  # Cache protocol research for 48 hours
                )

                findings.append(ResearchFinding(
                    title=f"{protocol_name} Security Analysis",
                    description=result.get("answer", ""),
                    severity="medium",
                    confidence=0.70,
                    research_source="perplexity",
                    references=result.get("sources", []),
                ))
            except Exception:
                logger.exception("Protocol research failed")

        self.findings.extend(findings)
        return findings

    async def correlate_cross_protocol(
        self,
        protocols: list[str],
    ) -> list[ResearchFinding]:
        """
        Identify vulnerabilities arising from cross-protocol interactions.

        Args:
            protocols: List of protocol names to analyze

        Returns:
            Cross-protocol vulnerability findings
        """
        logger.info(f"Analyzing cross-protocol risks for: {', '.join(protocols)}")

        if len(protocols) < 2:
            logger.warning("Need at least 2 protocols for correlation analysis")
            return []

        query = f"""
        Analyze security risks from interactions between these protocols: {', '.join(protocols)}.
        Focus on:
        1. Composability vulnerabilities
        2. Oracle dependencies and risks
        3. Shared infrastructure weaknesses
        4. Cross-protocol arbitrage attacks
        5. Integration vulnerability amplification

        Identify attack chains that exploit multiple protocols together.
        """

        findings = []

        if self.research_client:
            try:
                result = await self.research_client.research(
                    question=query,
                    context="Cross-protocol vulnerability correlation",
                    ttl_hours=24,
                )

                findings.append(ResearchFinding(
                    title=f"Cross-Protocol Risks: {', '.join(protocols)}",
                    description=result.get("answer", ""),
                    severity="high",
                    confidence=0.65,
                    research_source="perplexity",
                    references=result.get("sources", []),
                ))
            except Exception:
                logger.exception("Cross-protocol research failed")
        else:
            # Provide curated cross-protocol risk pattern
            findings.append(ResearchFinding(
                title="DeFi Composability Risks",
                description=(
                    "Protocols that integrate with multiple DeFi primitives face amplified risks "
                    "from composability. Key risks include oracle manipulation affecting multiple "
                    "dependent protocols, reentrancy through complex call chains, and flash loan "
                    "attacks exploiting integration assumptions."
                ),
                severity="high",
                confidence=0.75,
                research_source="curated",
                attack_vectors=[
                    "Multi-protocol oracle manipulation",
                    "Cross-protocol reentrancy chains",
                    "Flash loan attack amplification",
                    "Dependency exploitation cascades",
                ],
            ))

        self.findings.extend(findings)
        return findings

    async def generate_novel_hypotheses(
        self,
        target_contracts: list[str],
        context: str = "",
    ) -> list[dict[str, Any]]:
        """
        Generate novel vulnerability hypotheses using AI reasoning.

        Args:
            target_contracts: List of contract names/addresses
            context: Additional context about the target

        Returns:
            List of novel vulnerability hypotheses
        """
        logger.info(f"Generating novel hypotheses for {len(target_contracts)} contracts")

        # Combine emerging patterns with protocol-specific analysis
        emerging = await self.research_emerging_patterns(timeframe_days=90)

        # Convert findings to hypotheses
        hypotheses = []
        for finding in emerging:
            hypothesis = finding.to_hypothesis()
            hypothesis["novelty_score"] = 0.7  # Base novelty for emerging patterns
            hypothesis["source"] = "advanced_research"
            hypotheses.append(hypothesis)

        logger.info(f"Generated {len(hypotheses)} novel hypotheses")
        return hypotheses

    def get_all_findings(self) -> list[ResearchFinding]:
        """Get all research findings collected."""
        return self.findings

    def get_high_confidence_findings(
        self,
        min_confidence: float = 0.75,
    ) -> list[ResearchFinding]:
        """Get only high-confidence findings."""
        return [f for f in self.findings if f.confidence >= min_confidence]
