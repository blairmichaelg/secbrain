"""Bug bounty success metrics and learning system.

This module tracks success metrics for bug bounty hunting and implements
continuous learning from both successful and unsuccessful submissions.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BountySubmission:
    """Record of a bug bounty submission."""

    id: str
    program: str
    platform: str  # immunefi, hackerone, etc.
    submitted_at: str

    # Vulnerability details
    vulnerability_type: str
    severity: str
    title: str
    description: str

    # Submission outcome
    status: str  # submitted, accepted, rejected, duplicate, informative
    bounty_amount: float = 0.0
    feedback: str = ""

    # Analysis metadata
    detection_method: str = ""  # static_analysis, fuzzing, manual_review, etc.
    confidence_score: float = 0.0
    time_to_find_hours: float = 0.0

    # Learning data
    was_novel: bool = False
    similar_to: list[str] = field(default_factory=list)
    lessons_learned: list[str] = field(default_factory=list)


@dataclass
class ProgramMetrics:
    """Metrics for a specific bug bounty program."""

    program: str
    platform: str

    # Submission statistics
    total_submissions: int = 0
    accepted_submissions: int = 0
    rejected_submissions: int = 0
    duplicate_submissions: int = 0

    # Financial metrics
    total_earned: float = 0.0
    avg_bounty: float = 0.0
    highest_bounty: float = 0.0

    # Success rates
    acceptance_rate: float = 0.0
    avg_confidence_for_accepted: float = 0.0

    # Timing
    avg_time_to_find_hours: float = 0.0
    first_submission_at: str = ""
    last_submission_at: str = ""

    def update_from_submission(self, submission: BountySubmission) -> None:
        """Update metrics from a new submission."""
        self.total_submissions += 1

        if submission.status == "accepted":
            self.accepted_submissions += 1
            self.total_earned += submission.bounty_amount

            self.highest_bounty = max(self.highest_bounty, submission.bounty_amount)
        elif submission.status == "rejected":
            self.rejected_submissions += 1
        elif submission.status == "duplicate":
            self.duplicate_submissions += 1

        # Update rates
        if self.total_submissions > 0:
            self.acceptance_rate = self.accepted_submissions / self.total_submissions

        if self.accepted_submissions > 0:
            self.avg_bounty = self.total_earned / self.accepted_submissions

        # Update timestamps
        if not self.first_submission_at:
            self.first_submission_at = submission.submitted_at
        self.last_submission_at = submission.submitted_at


@dataclass
class VulnerabilityPatternLearning:
    """Learning data for a specific vulnerability pattern."""

    pattern_name: str

    # Detection statistics
    times_detected: int = 0
    times_submitted: int = 0
    times_accepted: int = 0
    times_rejected: int = 0

    # Success metrics
    avg_bounty: float = 0.0
    detection_effectiveness: float = 0.0  # accepted / submitted

    # Learning
    successful_detection_methods: list[str] = field(default_factory=list)
    common_false_positive_indicators: list[str] = field(default_factory=list)
    recommended_confidence_threshold: float = 0.70

    def update_from_submission(self, submission: BountySubmission) -> None:
        """Update learning from a submission."""
        self.times_submitted += 1

        if submission.status == "accepted":
            self.times_accepted += 1
            if submission.detection_method:
                self.successful_detection_methods.append(submission.detection_method)

            # Update avg bounty
            total = self.avg_bounty * (self.times_accepted - 1) + submission.bounty_amount
            self.avg_bounty = total / self.times_accepted
        elif submission.status == "rejected":
            self.times_rejected += 1

        # Update effectiveness
        if self.times_submitted > 0:
            self.detection_effectiveness = self.times_accepted / self.times_submitted


class BountyMetricsTracker:
    """
    Tracks and analyzes bug bounty hunting success metrics.

    Features:
    - Submission tracking and outcome analysis
    - Program-specific metrics
    - Vulnerability pattern learning
    - Success rate optimization
    - Continuous improvement insights
    """

    def __init__(self, metrics_dir: Path | str):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        # Storage files
        self.submissions_file = self.metrics_dir / "submissions.jsonl"
        self.program_metrics_file = self.metrics_dir / "program_metrics.json"
        self.pattern_learning_file = self.metrics_dir / "pattern_learning.json"

        # In-memory data
        self.submissions: list[BountySubmission] = []
        self.program_metrics: dict[str, ProgramMetrics] = {}
        self.pattern_learning: dict[str, VulnerabilityPatternLearning] = {}

        # Load existing data
        self._load_data()

    def _load_data(self) -> None:
        """Load existing metrics from disk."""
        # Load submissions
        if self.submissions_file.exists():
            with self.submissions_file.open() as f:
                for line in f:
                    data = json.loads(line)
                    self.submissions.append(BountySubmission(**data))

        # Load program metrics
        if self.program_metrics_file.exists():
            with self.program_metrics_file.open() as f:
                data = json.load(f)
                for key, value in data.items():
                    self.program_metrics[key] = ProgramMetrics(**value)

        # Load pattern learning
        if self.pattern_learning_file.exists():
            with self.pattern_learning_file.open() as f:
                data = json.load(f)
                for key, value in data.items():
                    self.pattern_learning[key] = VulnerabilityPatternLearning(**value)

        logger.info(f"Loaded {len(self.submissions)} submissions, "
                   f"{len(self.program_metrics)} programs, "
                   f"{len(self.pattern_learning)} patterns")

    def _save_data(self) -> None:
        """Save metrics to disk."""
        # Save submissions (append-only)
        # We only append new submissions, so this is called with new data

        # Save program metrics
        with self.program_metrics_file.open('w') as f:
            data = {k: asdict(v) for k, v in self.program_metrics.items()}
            json.dump(data, f, indent=2)

        # Save pattern learning
        with self.pattern_learning_file.open('w') as f:
            data = {k: asdict(v) for k, v in self.pattern_learning.items()}
            json.dump(data, f, indent=2)

    def record_submission(self, submission: BountySubmission) -> None:
        """Record a new bug bounty submission."""
        # Add to submissions
        self.submissions.append(submission)

        # Append to JSONL file
        with self.submissions_file.open('a') as f:
            f.write(json.dumps(asdict(submission)) + '\n')

        # Update program metrics
        program_key = f"{submission.platform}:{submission.program}"
        if program_key not in self.program_metrics:
            self.program_metrics[program_key] = ProgramMetrics(
                program=submission.program,
                platform=submission.platform,
            )
        self.program_metrics[program_key].update_from_submission(submission)

        # Update pattern learning
        vuln_type = submission.vulnerability_type
        if vuln_type not in self.pattern_learning:
            self.pattern_learning[vuln_type] = VulnerabilityPatternLearning(
                pattern_name=vuln_type,
            )
        self.pattern_learning[vuln_type].update_from_submission(submission)

        # Save updated data
        self._save_data()

        logger.info(f"Recorded submission: {submission.id} to {submission.program}")

    def get_program_metrics(self, program: str, platform: str) -> ProgramMetrics | None:
        """Get metrics for a specific program."""
        key = f"{platform}:{program}"
        return self.program_metrics.get(key)

    def get_pattern_learning(self, pattern: str) -> VulnerabilityPatternLearning | None:
        """Get learning data for a vulnerability pattern."""
        return self.pattern_learning.get(pattern)

    def get_overall_metrics(self) -> dict[str, Any]:
        """Get overall metrics across all programs."""
        total_submissions = len(self.submissions)
        if total_submissions == 0:
            return {
                "total_submissions": 0,
                "message": "No submissions recorded yet",
            }

        accepted = sum(1 for s in self.submissions if s.status == "accepted")
        rejected = sum(1 for s in self.submissions if s.status == "rejected")
        duplicates = sum(1 for s in self.submissions if s.status == "duplicate")

        total_earned = sum(s.bounty_amount for s in self.submissions if s.status == "accepted")
        avg_bounty = total_earned / accepted if accepted > 0 else 0

        return {
            "total_submissions": total_submissions,
            "accepted": accepted,
            "rejected": rejected,
            "duplicates": duplicates,
            "acceptance_rate": accepted / total_submissions if total_submissions > 0 else 0,
            "total_earned": total_earned,
            "avg_bounty": avg_bounty,
            "programs_participated": len(self.program_metrics),
            "patterns_learned": len(self.pattern_learning),
        }

    def get_top_performing_programs(self, limit: int = 5) -> list[ProgramMetrics]:
        """Get top programs by total earnings."""
        programs = sorted(
            self.program_metrics.values(),
            key=lambda p: p.total_earned,
            reverse=True,
        )
        return programs[:limit]

    def get_most_effective_patterns(self, limit: int = 10) -> list[VulnerabilityPatternLearning]:
        """Get most effective vulnerability patterns by acceptance rate."""
        patterns = sorted(
            self.pattern_learning.values(),
            key=lambda p: p.detection_effectiveness,
            reverse=True,
        )
        return patterns[:limit]

    def get_learning_insights(self) -> dict[str, Any]:
        """Generate learning insights for improvement."""
        insights = {
            "high_value_patterns": [],
            "low_confidence_patterns": [],
            "recommended_focus_areas": [],
            "common_rejection_reasons": [],
        }

        # High-value patterns (good bounty, good acceptance)
        for pattern in self.pattern_learning.values():
            if pattern.avg_bounty > 10000 and pattern.detection_effectiveness > 0.5:
                insights["high_value_patterns"].append({
                    "pattern": pattern.pattern_name,
                    "avg_bounty": pattern.avg_bounty,
                    "effectiveness": pattern.detection_effectiveness,
                })

        # Low-confidence patterns (high rejection rate)
        for pattern in self.pattern_learning.values():
            if pattern.detection_effectiveness < 0.3 and pattern.times_submitted > 3:
                insights["low_confidence_patterns"].append({
                    "pattern": pattern.pattern_name,
                    "effectiveness": pattern.detection_effectiveness,
                    "times_submitted": pattern.times_submitted,
                })

        # Recommended focus areas based on historical success
        top_patterns = self.get_most_effective_patterns(limit=5)
        insights["recommended_focus_areas"] = [
            {
                "pattern": p.pattern_name,
                "reason": f"High effectiveness ({p.detection_effectiveness:.1%}), "
                         f"avg bounty ${p.avg_bounty:.0f}",
            }
            for p in top_patterns if p.times_accepted > 0
        ]

        return insights

    def should_submit(
        self,
        vulnerability_type: str,
        confidence: float,
    ) -> dict[str, Any]:
        """
        Decide whether to submit based on learned patterns.

        Returns recommendation with reasoning.
        """
        pattern = self.get_pattern_learning(vulnerability_type)

        if not pattern or pattern.times_submitted < 3:
            # Not enough data, use conservative threshold
            should_submit = confidence >= 0.70
            reason = "Insufficient historical data, using default threshold (0.70)"
        else:
            threshold = pattern.recommended_confidence_threshold
            should_submit = confidence >= threshold

            reason = (
                f"Based on {pattern.times_submitted} submissions: "
                f"{pattern.detection_effectiveness:.1%} effectiveness, "
                f"${pattern.avg_bounty:.0f} avg bounty"
            )

        return {
            "should_submit": should_submit,
            "confidence": confidence,
            "threshold": pattern.recommended_confidence_threshold if pattern else 0.70,
            "reason": reason,
            "pattern_stats": asdict(pattern) if pattern else None,
        }
