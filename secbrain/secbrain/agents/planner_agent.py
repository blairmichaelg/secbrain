"""Planner agent - creates phased execution plans.

This module orchestrates the planning phase including:
- Multi-phase execution plan generation (recon → mapping → tests → triage → reporting)
- Integration with worker model and Perplexity research
- Advisor (Gemini) review and validation
- Strategic approach determination
"""

from __future__ import annotations

import json
from typing import Any

from secbrain.agents.base import AgentResult, BaseAgent


class PlannerAgent(BaseAgent):
    """
    Planner agent.

    Responsibilities:
    - Proposes a phased plan (recon → mapping → hypotheses → tests → triage → reporting)
    - Uses worker model + Perplexity research
    - Gets advisor (Gemini) review for the plan
    """

    name = "planner"
    phase = "plan"

    async def run(self, **kwargs: Any) -> AgentResult:
        """Create an execution plan for the bounty run."""
        self._log("starting_planning")

        if self._check_kill_switch():
            return self._failure("Kill-switch activated")

        ingest_data = kwargs.get("ingest_data", {})

        # Generate initial plan using worker model
        plan = await self._generate_plan(ingest_data)

        # Research for plan enhancement
        if self.research_client:
            plan = await self._enhance_with_research(plan, ingest_data)

        # Get advisor review
        review = await self._get_advisor_review(plan, ingest_data)

        # Adjust plan based on review
        if review.get("concerns"):
            plan = await self._adjust_plan(plan, review)

        # Store plan
        if self.storage:
            await self.storage.save_asset({
                "id": f"plan-{self.run_context.run_id}",
                "type": "plan",
                "value": json.dumps(plan),
                "metadata": {"review": review},
            })

        return self._success(
            message="Plan created and reviewed",
            data={
                "plan": plan,
                "review": review,
                "phases": [p["phase"] for p in plan.get("phases", [])],
            },
            next_actions=["recon"],
        )

    async def _generate_plan(self, ingest_data: dict[str, Any]) -> dict[str, Any]:
        """Generate initial execution plan using worker model."""
        domains = ingest_data.get("domains", [])
        focus_areas = ingest_data.get("focus_areas", [])

        prompt = f"""Create a security testing plan for a bug bounty program.

Target Domains: {domains}
Focus Areas: {focus_areas}
Program Rules: {ingest_data.get('rules', [])}

Create a phased plan with the following structure:
1. Recon Phase - Asset discovery and mapping
2. Hypothesis Phase - Identify potential vulnerability classes
3. Exploit Phase - Test hypotheses with payloads
4. Triage Phase - Validate and prioritize findings
5. Report Phase - Document and prepare submissions

For each phase, specify:
- Objectives
- Tools to use
- Time allocation
- Success criteria

Output as JSON with structure:
{{
  "phases": [
    {{
      "phase": "recon",
      "objectives": [...],
      "tools": [...],
      "time_estimate": "...",
      "success_criteria": [...]
    }}
  ],
  "priority_targets": [...],
  "risk_considerations": [...]
}}"""

        system = "You are a security testing planner. Create detailed, actionable plans. Output valid JSON only."

        response = await self._call_worker(prompt, system)

        try:
            # Extract JSON from response
            if "```" in response:
                json_str = response.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                return json.loads(json_str.strip())
            return json.loads(response)
        except json.JSONDecodeError:
            # Return a default plan
            return self._default_plan(domains)

    def _default_plan(self, domains: list[str]) -> dict[str, Any]:
        """Generate a default plan structure."""
        return {
            "phases": [
                {
                    "phase": "recon",
                    "objectives": ["Subdomain enumeration", "Port scanning", "Technology detection"],
                    "tools": ["subfinder", "httpx", "nmap"],
                    "time_estimate": "30 minutes",
                    "success_criteria": ["Complete asset inventory", "Technology stack identified"],
                },
                {
                    "phase": "hypothesis",
                    "objectives": ["Identify vulnerability classes", "Map attack surface"],
                    "tools": ["worker_model", "research"],
                    "time_estimate": "20 minutes",
                    "success_criteria": ["Hypothesis list generated", "Priorities assigned"],
                },
                {
                    "phase": "exploit",
                    "objectives": ["Test hypotheses", "Validate vulnerabilities"],
                    "tools": ["http_client", "nuclei"],
                    "time_estimate": "60 minutes",
                    "success_criteria": ["Hypotheses tested", "Findings documented"],
                },
                {
                    "phase": "triage",
                    "objectives": ["Validate findings", "Assess severity"],
                    "tools": ["advisor_model"],
                    "time_estimate": "15 minutes",
                    "success_criteria": ["Findings validated", "Severity assigned"],
                },
                {
                    "phase": "report",
                    "objectives": ["Create PoCs", "Write reports"],
                    "tools": ["worker_model", "research"],
                    "time_estimate": "30 minutes",
                    "success_criteria": ["Reports ready for submission"],
                },
            ],
            "priority_targets": domains[:3] if domains else [],
            "risk_considerations": [
                "Stay within scope boundaries",
                "Respect rate limits",
                "Avoid destructive testing",
            ],
        }

    async def _enhance_with_research(
        self,
        plan: dict[str, Any],
        ingest_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Enhance plan with research insights."""
        # Research effective techniques for the target type
        target_types = ingest_data.get("normalized", {}).get("target_types", ["web"])
        research = await self._research(
            question=f"What are the most effective bug bounty testing techniques for {', '.join(target_types)} targets?",
            context=f"Planning phase for: {ingest_data.get('program_name', 'unknown')}",
        )

        if research.get("answer"):
            plan["research_insights"] = research["answer"][:500]
            plan["research_sources"] = research.get("sources", [])

        return plan

    async def _get_advisor_review(
        self,
        plan: dict[str, Any],
        ingest_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Get advisor review of the plan."""
        if not self.advisor_model:
            return {"approved": True, "concerns": [], "suggestions": []}

        prompt = f"""Review this security testing plan for safety and effectiveness.

Program: {ingest_data.get('program_name', 'unknown')}
Scope: {ingest_data.get('domains', [])}
Rules: {ingest_data.get('rules', [])}

Plan:
{json.dumps(plan, indent=2)}

Evaluate:
1. Are all planned actions within scope?
2. Could any actions cause harm or service disruption?
3. Is the approach likely to find real vulnerabilities?
4. Are there any missing steps or considerations?

Respond with JSON:
{{
  "approved": true/false,
  "concerns": ["..."],
  "suggestions": ["..."],
  "risk_level": "low/medium/high"
}}"""

        response = await self._call_advisor(prompt)

        try:
            if "```" in response:
                json_str = response.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                return json.loads(json_str.strip())
            return json.loads(response)
        except json.JSONDecodeError:
            return {"approved": True, "concerns": [], "suggestions": [], "risk_level": "medium"}

    async def _adjust_plan(
        self,
        plan: dict[str, Any],
        review: dict[str, Any],
    ) -> dict[str, Any]:
        """Adjust plan based on advisor review."""
        plan["advisor_concerns"] = review.get("concerns", [])
        plan["advisor_suggestions"] = review.get("suggestions", [])
        plan["risk_level"] = review.get("risk_level", "medium")
        plan["advisor_approved"] = review.get("approved", False)

        return plan
