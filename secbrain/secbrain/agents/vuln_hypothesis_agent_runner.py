"""Vulnerability hypothesis execution logic."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import TYPE_CHECKING, Any

from eth_utils import is_address, to_checksum_address
from jsonschema import ValidationError, validate

from secbrain.agents.base import AgentResult
from secbrain.agents.oracle_manipulation_detector import OracleManipulationDetector
from secbrain.agents.vuln_hypothesis_agent_base import (
    ABI_JSON_SIZE_LIMIT,
    ABI_PREVIEW_MAX_ENTRIES,
    ABI_PREVIEW_REDUCED_ENTRIES,
    FUNCTIONS_PREVIEW_LIMIT,
    ProtocolProfile,
)

if TYPE_CHECKING:
    from secbrain.agents.vuln_hypothesis_agent_base import BaseVulnHypothesisAgent
    _Base = BaseVulnHypothesisAgent
else:
    _Base = object

logger = logging.getLogger(__name__)

class VulnHypothesisRunnerMixin(_Base):
    """Mixin for hypothesis generation orchestration and LLM interaction."""

    async def run(self, **kwargs: Any) -> AgentResult:
        """Generate vulnerability hypotheses."""
        self._log("starting_hypothesis_generation")

        if self._check_kill_switch():
            return self._failure("Kill-switch activated")

        recon_data = kwargs.get("recon_data", {})
        assets = recon_data.get("assets", [])
        technologies = recon_data.get("technologies", [])

        if not assets:
            return self._failure("No assets available for hypothesis generation")

        all_hypotheses: list[dict[str, Any]] = []
        live_hosts = [a for a in assets if a.get("type") == "live_host"]
        contract_assets = [a for a in assets if a.get("type") == "contract"]

        host_sem = asyncio.Semaphore(5)

        async def _gen_host(asset: dict[str, Any]) -> list[dict[str, Any]]:
            async with host_sem:
                return await self._generate_hypotheses_for_asset(asset, technologies)

        host_tasks = [asyncio.create_task(_gen_host(h)) for h in live_hosts[:10]]
        if host_tasks:
            host_results = await asyncio.gather(*host_tasks)
            for hs in host_results:
                all_hypotheses.extend(hs or [])

        if contract_assets:
            contract_batches = await self._generate_batch_hypotheses(contract_assets, batch_size=10)
            for batch in contract_batches:
                all_hypotheses.extend(batch or [])

        if all_hypotheses and self.research_client:
            all_hypotheses = await self._research_validate_hypotheses(all_hypotheses)

        ranked = self._rank_hypotheses(all_hypotheses)
        confidence_threshold = self.CONFIDENCE_THRESHOLD
        filtered = [h for h in ranked if h.get("confidence", 0) >= confidence_threshold]
        top_hypotheses = filtered[:5]

        if not top_hypotheses and contract_assets:
            self._log("generating_fallback_hypotheses", contract_count=len(contract_assets))
            fallback_hypotheses = self._generate_fallback_hypotheses(contract_assets[:3])
            all_hypotheses.extend(fallback_hypotheses)
            ranked = self._rank_hypotheses(all_hypotheses)
            filtered = [h for h in ranked if h.get("confidence", 0) >= confidence_threshold]
            top_hypotheses = filtered[:5]

        review = await self._advisor_review_hypotheses(top_hypotheses)

        missing_targets = [h for h in ranked if not h.get("contract_address") or not h.get("function_signature")]
        missing_summary = {
            "missing_contract_or_function": len(missing_targets),
            "total_hypotheses": len(ranked),
        }

        if self.storage:
            for hyp in all_hypotheses:
                await self.storage.save_hypothesis(hyp)

        return self._success(
            message=f"Generated {len(all_hypotheses)} hypotheses",
            data={
                "hypotheses": ranked,
                "top_hypotheses": top_hypotheses,
                "review": review,
                "by_vuln_type": self._group_by_type(all_hypotheses),
                "missing_targets": missing_summary,
            },
            next_actions=["exploit"],
        )

    async def _generate_batch_hypotheses(
        self,
        contracts: list[dict[str, Any]],
        batch_size: int = 10,
    ) -> list[list[dict[str, Any]]]:
        """Generate hypotheses for multiple contracts in batches."""
        results: list[list[dict[str, Any]]] = []

        for i in range(0, len(contracts), batch_size):
            batch = contracts[i : i + batch_size]
            batch_tasks = [
                asyncio.create_task(self._generate_hypotheses_for_contract_asset(contract))
                for contract in batch
            ]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for contract, result in zip(batch, batch_results, strict=False):
                if isinstance(result, Exception):
                    self._log_error("batch_hypothesis_failed", contract=contract.get("name"), error=str(result))
                    results.append([])
                else:
                    results.append(result or [])
        return results

    async def _generate_hypotheses_for_contract_asset(self, asset: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate vulnerability hypotheses for a single contract asset."""
        try:
            contract_address = self._checksum_address(asset.get("value"))
        except (ValueError, TypeError) as e:
            self._log_error("invalid_contract_address_skipping", contract=asset.get("name"), address=asset.get("value"), error=str(e))
            return []

        address = contract_address
        name = asset.get("name", "")
        chain_id = asset.get("chain_id")
        foundry_profile = asset.get("foundry_profile") or asset.get("profile")
        metadata = asset.get("metadata", {})
        functions = metadata.get("functions", []) or []
        abi = metadata.get("abi", []) or []
        solc = metadata.get("solc")

        scope_profit_tokens = []
        try:
            scope_profit_tokens = getattr(getattr(self.run_context, "scope", None), "profit_tokens", None) or []
        except Exception:
            scope_profit_tokens = []

        static_hypotheses = [
            hyp
            for hyp in self._static_vulnerability_patterns(
                abi=abi,
                functions=functions,
                metadata=metadata,
                contract_address=address,
                chain_id=chain_id,
                foundry_profile=foundry_profile,
                solc=solc,
                scope_profit_tokens=scope_profit_tokens,
            )
            if self._feasibility_gate(hyp, abi, functions) and self._validate_hypothesis(hyp)
        ]

        static_conf_ok = [h for h in static_hypotheses if float(h.get("confidence", 0)) >= 0.6]
        if len(static_conf_ok) >= 3:
            return static_hypotheses

        functions_preview = functions[:FUNCTIONS_PREVIEW_LIMIT]
        abi_preview = abi[:ABI_PREVIEW_MAX_ENTRIES]
        try:
            if len(json.dumps(abi_preview)) > ABI_JSON_SIZE_LIMIT:
                abi_preview = abi[:ABI_PREVIEW_REDUCED_ENTRIES]
        except Exception:
            abi_preview = abi[:ABI_PREVIEW_REDUCED_ENTRIES]

        classification = (asset.get("metadata", {}) or {}).get("classification", {})
        protocol_type = classification.get("protocol_type", "generic")
        profile = ProtocolProfile.from_type(protocol_type)
        pattern_hint = ", ".join(profile.patterns)
        pool_registry = None
        try:
            pool_registry = getattr(getattr(self.run_context, "scope", None), "pool_registry", None)
        except Exception:
            pool_registry = None

        lower_functions = [fn.lower() for fn in functions]
        research_context = ""
        if self.research_client and pattern_hint:
            primary_pattern = profile.patterns[0] if profile.patterns else protocol_type
            try:
                research_result = await self.research_client.research_attack_vectors(
                    vuln_type=primary_pattern,
                    run_context=self.run_context,
                    contract_pattern=f"{protocol_type} with functions: {', '.join(functions_preview[:5])}",
                )
                if not research_result.get("error") and not research_result.get("limited"):
                    research_context = f"\n\nReal-world attack vectors for {primary_pattern}:\n{research_result.get('answer', '')[:400]}\n"
            except Exception as e:
                self._log_error("research_attack_vectors_failed", error=str(e))

        system_prompt = """You are a senior smart contract security researcher. 
Your goal is to generate high-quality vulnerability hypotheses using the Plan-and-Solve architecture.

Follow these steps for every analysis:
1. **Understand**: Analyze the protocol type, sample functions, and real-world attack context provided.
2. **Plan**: Outline a strategy to find specific vulnerabilities common in this protocol type (e.g., flash-loan oracle manipulation for DeFi, message forgery for bridges).
3. **Solve**: Generate 3-5 concrete hypotheses based on your plan.

Each hypothesis must be a JSON object with:
- `vuln_type`: One of the predefined vulnerability types.
- `confidence`: 0.0 to 1.0.
- `contract_address`: The target contract.
- `function_signature`: The specific function to target.
- `rationale`: Why this is likely vulnerable.
- `test_approach`: How to verify it using a Foundry test.
- `exploit_notes`: Key technical details for payload generation.

Return ONLY a JSON array of hypotheses."""

        prompt = f"""Target Contract: {name} ({address})
Chain ID: {chain_id}
Protocol Type: {protocol_type}
Functions Sample: {', '.join(functions_preview[:15])}

{research_context}

Deconstruct the contract's purpose and provide your Plan-and-Solve analysis."""

        async with self._contract_llm_sem:
            response = await self._call_worker(prompt, system=system_prompt, tier="fast")

        raw_hypotheses = await self._parse_hypotheses_with_validation(
            response=response,
            contract_name=name,
            chain_id=chain_id,
            functions=functions,
            address=address,
            functions_preview=functions_preview,
        )

        combined_hypotheses = list(static_hypotheses)
        if raw_hypotheses:
            hypotheses: list[dict[str, Any]] = []
            for h in raw_hypotheses:
                func_sig = h.get("function_signature") or (functions[0] if functions else None)
                fn_name = (str(func_sig).split("(")[0] if func_sig else "").strip()
                abi_entry = self._get_abi_entry(fn_name, abi)

                state_mutability = ""
                param_types = []
                returns_value = False
                is_payable = False
                writes_state = False
                if abi_entry:
                    state_mutability = str(abi_entry.get("stateMutability") or "")
                    inputs = abi_entry.get("inputs") or []
                    outputs = abi_entry.get("outputs") or []
                    param_types = [str(inp.get("type")) for inp in inputs if isinstance(inp, dict) and inp.get("type")]
                    returns_value = isinstance(outputs, list) and len(outputs) > 0
                    is_payable = state_mutability == "payable"
                    writes_state = state_mutability in {"nonpayable", "payable"}

                oracle_detector = OracleManipulationDetector()
                oracle_info = oracle_detector.detect_oracle_dependency(abi, functions)
                exploit_notes = h.get("exploit_notes", [])
                exploit_body = h.get("exploit_body")
                if oracle_info.get("has_oracle") and h.get("vuln_type") == "oracle_manipulation":
                    exploit_body = oracle_detector.generate_manipulation_exploit(
                        {"contract_address": h.get("contract_address") or address},
                        oracle_info,
                        pool_registry=pool_registry,
                    )
                    exploit_notes = exploit_notes or ["Flash swap to skew reserves", "Oracle reads manipulated price", "Execute price-dependent path"]

                normalized_addr = self._validate_and_normalize_address(h.get("contract_address") or contract_address)
                if not normalized_addr:
                    continue

                candidate = {
                    "id": f"hyp-{uuid.uuid4().hex[:8]}",
                    "asset_id": asset.get("id"),
                    "target": f"{name}@{address}" if name else address,
                    "vuln_type": h.get("vuln_type", "unknown"),
                    "confidence": min(max(float(h.get("confidence", 0.5)), 0.0), 1.0),
                    "rationale": h.get("rationale", ""),
                    "test_approach": h.get("test_approach", ""),
                    "contract_address": normalized_addr,
                    "chain_id": h.get("chain_id") or chain_id,
                    "function_signature": func_sig,
                    "foundry_profile": foundry_profile,
                    "solc": solc,
                    "abi": abi,
                    "oracle_functions": oracle_info.get("oracle_functions"),
                    "profit_tokens": scope_profit_tokens,
                    "exploit_notes": exploit_notes,
                    "expected_profit_hint_eth": h.get("expected_profit_hint_eth"),
                    "function_state_mutability": state_mutability,
                    "function_is_payable": is_payable,
                    "function_writes_state": writes_state,
                    "function_returns_value": returns_value,
                    "function_param_count": len(param_types),
                    "function_param_types": param_types,
                    "exploit_body": exploit_body,
                    "status": "pending",
                }

                if not self._feasibility_gate(candidate, abi, functions):
                    continue
                if not self._validate_hypothesis(candidate):
                    continue

                hypotheses.append(candidate)

            hypotheses.extend(
                self._heuristic_enrich_hypotheses(
                    hypotheses,
                    address=address,
                    name=name,
                    chain_id=chain_id,
                    foundry_profile=foundry_profile,
                    solc=solc,
                    abi=abi,
                    functions=functions,
                    scope_profit_tokens=scope_profit_tokens,
                )
            )

            # Check for missing oracle hypothesis
            oracle_info = self._oracle_detector.detect_oracle_dependency(abi, functions)
            if oracle_info.get("has_oracle"):
                oracle_sig = oracle_info["oracle_functions"][0] if oracle_info["oracle_functions"] else (functions[0] if functions else None)
                exploit_body = self._oracle_detector.generate_manipulation_exploit(
                    {"contract_address": address},
                    oracle_info,
                    pool_registry=pool_registry,
                )
                normalized_addr = self._validate_and_normalize_address(address)
                if normalized_addr:
                    hypotheses.append({
                        "id": f"hyp-{uuid.uuid4().hex[:8]}",
                        "asset_id": asset.get("id"),
                        "target": f"{name}@{address}" if name else address,
                        "vuln_type": "oracle_manipulation",
                        "confidence": 0.85,
                        "rationale": f"Detected oracle functions: {', '.join(oracle_info['oracle_functions'])}",
                        "test_approach": "Manipulate oracle via flash swap and trigger price-dependent path.",
                        "contract_address": normalized_addr,
                        "chain_id": chain_id,
                        "function_signature": oracle_sig,
                        "foundry_profile": foundry_profile,
                        "solc": solc,
                        "abi": abi,
                        "profit_tokens": scope_profit_tokens,
                        "exploit_notes": ["Flash swap to skew reserves", "Oracle reads manipulated price", "Execute settlement with favorable price"],
                        "expected_profit_hint_eth": 5.0,
                        "status": "pending",
                        "exploit_body": exploit_body,
                    })

            combined_hypotheses.extend(hypotheses[: profile.budget])
        else:
            normalized_addr = self._validate_and_normalize_address(address)
            if normalized_addr:
                combined_hypotheses.append({
                    "id": f"hyp-{uuid.uuid4().hex[:8]}",
                    "asset_id": asset.get("id"),
                    "target": f"{name}@{address}" if name else address,
                    "vuln_type": "generic_contract",
                    "confidence": 0.3,
                    "rationale": "Generic on-chain testing hypothesis",
                    "test_approach": "Write a forked Foundry test for common exploit patterns",
                    "contract_address": normalized_addr,
                    "chain_id": chain_id,
                    "function_signature": functions[0] if functions else None,
                    "foundry_profile": foundry_profile,
                    "solc": solc,
                    "abi": abi,
                    "profit_tokens": scope_profit_tokens,
                    "status": "pending",
                })
        return combined_hypotheses

    async def _parse_hypotheses_with_validation(
        self,
        response: str,
        contract_name: str,
        chain_id: int | None,
        functions: list[str],
        address: str,
        functions_preview: list[str],
        max_retries: int = 2,
    ) -> list[dict[str, Any]]:
        """Parse hypothesis JSON with schema validation and corrective prompting."""

        def _extract_json_array(text: str) -> list[dict[str, Any]]:
            if not text:
                raise json.JSONDecodeError("empty", text, 0)
            s = text.strip()
            if "```" in s:
                parts = s.split("```")
                for i in range(1, len(parts), 2):
                    block = parts[i].strip()
                    if block.startswith("json"): block = block[4:].strip()
                    elif block.startswith("javascript"): block = block[10:].strip()
                    try:
                        data = json.loads(block)
                        if isinstance(data, list): return [item for item in data if isinstance(item, dict)]
                        if isinstance(data, dict): return [data]
                    except (json.JSONDecodeError, ValueError):
                        start = block.find("[")
                        end = block.rfind("]")
                        if start != -1 and end != -1 and end > start:
                            try:
                                data = json.loads(block[start : end + 1])
                                if isinstance(data, list): return [item for item in data if isinstance(item, dict)]
                            except (json.JSONDecodeError, ValueError): continue
            start = s.find("[")
            end = s.rfind("]")
            if start != -1 and end != -1 and end > start:
                try:
                    data = json.loads(s[start : end + 1])
                    if isinstance(data, list):
                        out = [item for item in data if isinstance(item, dict)]
                        if out: return out
                except (json.JSONDecodeError, ValueError): pass
            try:
                data = json.loads(s)
                if isinstance(data, list): return [item for item in data if isinstance(item, dict)]
                if isinstance(data, dict): return [data]
            except (json.JSONDecodeError, ValueError): pass
            raise json.JSONDecodeError("Could not extract valid JSON array", text, 0)

        parsed: list[dict[str, Any]] = []
        allowed_vuln_types = set(self.HYPOTHESIS_SCHEMA["items"]["properties"]["vuln_type"]["enum"])

        def _normalize_item(item: dict[str, Any]) -> dict[str, Any]:
            out = dict(item)
            if "vuln_type" not in out and "vulnerability" in out:
                out["vuln_type"] = str(out.get("vulnerability") or "").strip().lower()
            if "function_signature" not in out and "function" in out:
                out["function_signature"] = out.get("function")
            if "confidence" not in out or out.get("confidence") is None:
                out["confidence"] = 0.5
            vt = str(out.get("vuln_type") or "").strip().lower()
            if not vt: vt = "generic_contract"
            aliases = {
                "owner_privilege_escalation": "access_control",
                "privilege_escalation": "access_control",
                "admin_takeover": "access_control",
                "governance_hijack": "flash_loan_governance_attack",
                "price_oracle": "oracle_manipulation",
            }
            vt = aliases.get(vt, vt)
            if vt not in allowed_vuln_types: vt = "generic_contract"
            out["vuln_type"] = vt
            return out

        for attempt in range(max_retries):
            try:
                raw = _extract_json_array(response)
                normalized = [_normalize_item(i) for i in raw]
                validate(instance=normalized, schema=self.HYPOTHESIS_SCHEMA)
                parsed = normalized
                break
            except (json.JSONDecodeError, ValidationError) as e:
                if attempt < max_retries - 1:
                    response = await self._call_worker(f"JSON response malformed or failed validation: {e!s}. Fix and return ONLY a JSON array.", tier="fast")
                continue
            except Exception:
                if attempt == max_retries - 1: parsed = []
                continue
        return parsed

    def _checksum_address(self, address: str | None) -> str:
        if not address: raise ValueError("cannot be None or empty")
        addr = address.strip()
        if not addr.startswith("0x"): raise ValueError("start with '0x'")
        if len(addr) != 42: raise ValueError("42 characters")
        if not is_address(addr): raise ValueError(f"Invalid format: {address}")
        return to_checksum_address(addr)

    def _validate_and_normalize_address(self, address: str | None) -> str | None:
        try:
            return self._checksum_address(address)
        except (ValueError, TypeError):
            return None

    async def _research_validate_hypotheses(self, hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_type: dict[str, list[dict[str, Any]]] = {}
        for h in hypotheses:
            vtype = h.get("vuln_type", "unknown")
            if vtype not in by_type: by_type[vtype] = []
            by_type[vtype].append(h)
        for vtype, hyps in list(by_type.items())[:3]:
            research = await self._research(question=f"Testing techniques for {vtype} in web apps.", context=f"Validating {len(hyps)} hypotheses.")
            for h in hyps: h["research_context"] = research.get("answer", "")[:200]
        return hypotheses

    async def _advisor_review_hypotheses(self, hypotheses: list[dict[str, Any]]) -> dict[str, Any]:
        if not self.advisor_model or not hypotheses: return {"reviewed": False}
        prompt = f"Review these vulnerability hypotheses: {json.dumps(hypotheses[:10])}. Respond with priority_hypotheses, skip_hypotheses, safety_concerns, recommendations."
        response = await self._call_advisor(prompt)
        try:
            if "```" in response:
                json_str = response.split("```")[1]
                if json_str.startswith("json"): json_str = json_str[4:]
                return json.loads(json_str.strip())
            return json.loads(response)
        except json.JSONDecodeError: return {"reviewed": True, "error": "Failed to parse advisor response"}

    def _generate_fallback_hypotheses(self, contract_assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        fallback_hypotheses = []
        for asset in contract_assets:
            metadata = asset.get("metadata", {}) or {}
            address = metadata.get("address") or asset.get("value", "")
            chain_id = metadata.get("chain_id", 1)
            functions = metadata.get("functions", [])
            protocol_type = (metadata.get("classification", {}) or {}).get("protocol_type", "generic")
            profile = ProtocolProfile.from_type(protocol_type)
            for pattern in profile.patterns[:2]:
                fallback_hypotheses.append({
                    "id": str(uuid.uuid4()),
                    "vuln_type": pattern,
                    "confidence": 0.45,
                    "contract_address": address,
                    "chain_id": chain_id,
                    "function_signature": functions[0] if functions else None,
                    "rationale": f"Fallback for {protocol_type}. Pattern: {pattern}.",
                    "status": "pending",
                    "is_fallback": True,
                })
        return fallback_hypotheses

    async def _generate_hypotheses_for_asset(self, asset: dict[str, Any], technologies: list[str]) -> list[dict[str, Any]]:
        url = asset.get("value", "")
        metadata = asset.get("metadata", {})
        tech_list = metadata.get("technologies", []) + technologies
        prompt = f"Analyze web asset: {url}. Tech: {tech_list[:10]}. Return JSON array of hypotheses."
        response = await self._call_worker(prompt, tier="fast")
        try:
            if "```" in response:
                json_str = response.split("```")[1]
                if json_str.startswith("json"): json_str = json_str[4:]
                raw = json.loads(json_str.strip())
            else:
                raw = json.loads(response)
            return [{
                "id": f"hyp-{uuid.uuid4().hex[:8]}",
                "asset_id": asset.get("id"),
                "target": url,
                "vuln_type": h.get("vuln_type", "unknown"),
                "confidence": min(max(float(h.get("confidence", 0.5)), 0.0), 1.0),
                "status": "pending",
            } for h in raw]
        except (json.JSONDecodeError, ValueError):
            return [{"id": f"hyp-{uuid.uuid4().hex[:8]}", "asset_id": asset.get("id"), "target": url, "vuln_type": "generic", "confidence": 0.3, "status": "pending"}]
