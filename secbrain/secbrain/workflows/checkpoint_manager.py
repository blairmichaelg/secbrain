"""Checkpoint and resume capability for long-running workflows."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class Checkpoint:
    """Workflow checkpoint data."""

    run_id: str
    current_phase: str
    completed_phases: list[str]
    phase_data: dict[str, dict[str, Any]]
    timestamp: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert checkpoint to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Checkpoint:
        """Create checkpoint from dictionary."""
        return cls(
            run_id=data["run_id"],
            current_phase=data["current_phase"],
            completed_phases=data["completed_phases"],
            phase_data=data["phase_data"],
            timestamp=data["timestamp"],
            metadata=data.get("metadata", {}),
        )


class CheckpointManager:
    """
    Manage workflow checkpoints for resume capability.

    Features:
    - Save workflow state at phase boundaries
    - Resume from last successful checkpoint
    - Automatic checkpoint cleanup
    - Checkpoint versioning
    """

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.checkpoint_dir = workspace_path / ".checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        run_id: str,
        current_phase: str,
        completed_phases: list[str],
        phase_data: dict[str, dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """
        Save a workflow checkpoint.

        Args:
            run_id: Unique run identifier
            current_phase: Current phase being executed
            completed_phases: List of completed phases
            phase_data: Data from completed phases
            metadata: Optional additional metadata

        Returns:
            Path to saved checkpoint file
        """
        checkpoint = Checkpoint(
            run_id=run_id,
            current_phase=current_phase,
            completed_phases=completed_phases,
            phase_data=phase_data,
            timestamp=datetime.now(UTC).isoformat(),
            metadata=metadata or {},
        )

        checkpoint_file = self.checkpoint_dir / f"{run_id}_latest.json"
        checkpoint_file.write_text(json.dumps(checkpoint.to_dict(), indent=2))

        # Also save timestamped version for history
        timestamped_file = self.checkpoint_dir / f"{run_id}_{current_phase}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
        timestamped_file.write_text(json.dumps(checkpoint.to_dict(), indent=2))

        return checkpoint_file

    def load_checkpoint(self, run_id: str) -> Checkpoint | None:
        """
        Load the latest checkpoint for a run.

        Args:
            run_id: Unique run identifier

        Returns:
            Checkpoint if found, None otherwise
        """
        checkpoint_file = self.checkpoint_dir / f"{run_id}_latest.json"
        if not checkpoint_file.exists():
            return None

        try:
            data = json.loads(checkpoint_file.read_text())
            return Checkpoint.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def has_checkpoint(self, run_id: str) -> bool:
        """Check if a checkpoint exists for a run."""
        checkpoint_file = self.checkpoint_dir / f"{run_id}_latest.json"
        return checkpoint_file.exists()

    def delete_checkpoint(self, run_id: str) -> None:
        """Delete checkpoint for a run."""
        checkpoint_file = self.checkpoint_dir / f"{run_id}_latest.json"
        if checkpoint_file.exists():
            checkpoint_file.unlink()

    def cleanup_old_checkpoints(self, max_age_days: int = 7) -> int:
        """
        Clean up old checkpoint files.

        Args:
            max_age_days: Delete checkpoints older than this many days

        Returns:
            Number of checkpoints deleted
        """
        deleted = 0
        cutoff = datetime.now(UTC).timestamp() - (max_age_days * 86400)

        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            if checkpoint_file.stat().st_mtime < cutoff:
                checkpoint_file.unlink()
                deleted += 1

        return deleted

    def list_checkpoints(self) -> list[tuple[str, datetime]]:
        """
        List all available checkpoints.

        Returns:
            List of (run_id, timestamp) tuples
        """
        checkpoints = []
        for checkpoint_file in self.checkpoint_dir.glob("*_latest.json"):
            run_id = checkpoint_file.stem.replace("_latest", "")
            try:
                data = json.loads(checkpoint_file.read_text())
                timestamp = datetime.fromisoformat(data["timestamp"])
                checkpoints.append((run_id, timestamp))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

        return sorted(checkpoints, key=lambda x: x[1], reverse=True)
