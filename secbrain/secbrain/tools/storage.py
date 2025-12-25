"""Storage layer for SecBrain (JSON/SQLite)."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, LiteralString

try:
    import aiosqlite
except ModuleNotFoundError:  # pragma: no cover
    aiosqlite = None  # type: ignore[assignment]

if TYPE_CHECKING:

    from secbrain.core.context import RunContext


class WorkspaceStorage:
    """
    Workspace storage for SecBrain runs.

    Stores:
    - Recon results
    - Hypotheses
    - Findings
    - Run metadata
    """

    def __init__(self, workspace_path: Path | RunContext, run_id: str | None = None):
        if run_id is None and hasattr(workspace_path, "workspace_path"):
            rc: RunContext = workspace_path  # type: ignore[assignment]
            self.workspace_path: Path = rc.workspace_path
            self.run_id: str = rc.run_id
        else:
            if run_id is None:
                raise TypeError("WorkspaceStorage requires run_id when workspace_path is a Path")
            self.workspace_path = workspace_path  # type: ignore[assignment]
            self.run_id = run_id
        self.db_path: Path = self.workspace_path / "secbrain.db"
        self._db: Any = None
        self._sqlite_backend: str = "aiosqlite" if aiosqlite is not None else "sqlite3"

    async def _execute(self, sql: LiteralString, params: tuple[Any, ...] = ()) -> Any:
        """Execute a SQL query with parameterized values.

        Args:
            sql: SQL query as a literal string (prevents SQL injection)
            params: Query parameters to be safely substituted

        Returns:
            Database cursor with query results
        """
        if self._db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        if self._sqlite_backend == "aiosqlite":
            return await self._db.execute(sql, params)
        return await asyncio.to_thread(self._db.execute, sql, params)

    async def _executescript(self, sql: LiteralString) -> None:
        """Execute a SQL script (multiple statements).

        Args:
            sql: SQL script as a literal string (prevents SQL injection)
        """
        if self._db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        if self._sqlite_backend == "aiosqlite":
            await self._db.executescript(sql)
            return
        await asyncio.to_thread(self._db.executescript, sql)

    async def _commit(self) -> None:
        """Commit pending database transactions."""
        if self._db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        if self._sqlite_backend == "aiosqlite":
            await self._db.commit()
            return
        await asyncio.to_thread(self._db.commit)

    async def initialize(self) -> None:
        """Initialize the storage database."""
        if aiosqlite is not None:
            self._db = await aiosqlite.connect(self.db_path)
        else:
            import sqlite3
            self._db = sqlite3.connect(self.db_path, check_same_thread=False)
        await self._create_tables()

    async def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        await self._executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                start_time TEXT,
                end_time TEXT,
                status TEXT,
                scope_hash TEXT,
                metadata TEXT
            );

            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                run_id TEXT,
                type TEXT,
                value TEXT,
                technologies TEXT,
                metadata TEXT,
                discovered_at TEXT,
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            );

            CREATE TABLE IF NOT EXISTS hypotheses (
                id TEXT PRIMARY KEY,
                run_id TEXT,
                asset_id TEXT,
                vuln_type TEXT,
                confidence REAL,
                rationale TEXT,
                status TEXT,
                result TEXT,
                created_at TEXT,
                FOREIGN KEY (run_id) REFERENCES runs(run_id),
                FOREIGN KEY (asset_id) REFERENCES assets(id)
            );

            CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY,
                run_id TEXT,
                title TEXT,
                severity TEXT,
                status TEXT,
                vuln_type TEXT,
                target TEXT,
                description TEXT,
                evidence TEXT,
                created_at TEXT,
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            );

            CREATE TABLE IF NOT EXISTS tool_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                tool TEXT,
                action TEXT,
                target TEXT,
                success INTEGER,
                duration_ms REAL,
                timestamp TEXT,
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            );

            CREATE INDEX IF NOT EXISTS idx_assets_run ON assets(run_id);
            CREATE INDEX IF NOT EXISTS idx_hypotheses_run ON hypotheses(run_id);
            CREATE INDEX IF NOT EXISTS idx_findings_run ON findings(run_id);
            CREATE INDEX IF NOT EXISTS idx_tool_calls_run ON tool_calls(run_id);
        """)
        await self._commit()

    async def start_run(self, scope_hash: str, metadata: dict[str, Any] | None = None) -> None:
        """Record the start of a run."""
        await self._execute(
            """
            INSERT OR REPLACE INTO runs (run_id, start_time, status, scope_hash, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                self.run_id,
                datetime.now().isoformat(),
                "running",
                scope_hash,
                json.dumps(metadata or {}),
            ),
        )
        await self._commit()

    async def end_run(self, status: str = "completed") -> None:
        """Record the end of a run."""
        await self._execute(
            """
            UPDATE runs SET end_time = ?, status = ? WHERE run_id = ?
            """,
            (datetime.now().isoformat(), status, self.run_id),
        )
        await self._commit()

    async def save_asset(self, asset: dict[str, Any]) -> None:
        """Save a discovered asset."""
        await self._execute(
            """
            INSERT OR REPLACE INTO assets (id, run_id, type, value, technologies, metadata, discovered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                asset.get("id"),
                self.run_id,
                asset.get("type"),
                asset.get("value"),
                json.dumps(asset.get("technologies", [])),
                json.dumps(asset.get("metadata", {})),
                datetime.now().isoformat(),
            ),
        )
        await self._commit()

    async def save_assets(self, assets: list[dict[str, Any]]) -> None:
        """Save multiple assets."""
        for asset in assets:
            await self.save_asset(asset)

    async def get_assets(self, asset_type: str | None = None) -> list[dict[str, Any]]:
        """Get assets, optionally filtered by type."""
        if asset_type:
            cursor = await self._execute(
                "SELECT * FROM assets WHERE run_id = ? AND type = ?",
                (self.run_id, asset_type),
            )
        else:
            cursor = await self._execute(
                "SELECT * FROM assets WHERE run_id = ?",
                (self.run_id,),
            )

        if self._sqlite_backend == "aiosqlite":
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        else:
            rows = await asyncio.to_thread(cursor.fetchall)
            columns = [desc[0] for desc in cursor.description]

        assets = []
        for row in rows:
            asset = dict(zip(columns, row))
            asset["technologies"] = json.loads(asset.get("technologies", "[]"))
            asset["metadata"] = json.loads(asset.get("metadata", "{}"))
            assets.append(asset)

        return assets

    async def save_hypothesis(self, hypothesis: dict[str, Any]) -> None:
        """Save a vulnerability hypothesis."""
        await self._execute(
            """
            INSERT OR REPLACE INTO hypotheses
            (id, run_id, asset_id, vuln_type, confidence, rationale, status, result, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                hypothesis.get("id"),
                self.run_id,
                hypothesis.get("asset_id"),
                hypothesis.get("vuln_type"),
                hypothesis.get("confidence", 0.5),
                hypothesis.get("rationale", ""),
                hypothesis.get("status", "pending"),
                json.dumps(hypothesis.get("result", {})),
                datetime.now().isoformat(),
            ),
        )
        await self._commit()

    async def get_hypotheses(self, status: str | None = None) -> list[dict[str, Any]]:
        """Get hypotheses, optionally filtered by status."""
        if status:
            cursor = await self._execute(
                "SELECT * FROM hypotheses WHERE run_id = ? AND status = ?",
                (self.run_id, status),
            )
        else:
            cursor = await self._execute(
                "SELECT * FROM hypotheses WHERE run_id = ?",
                (self.run_id,),
            )

        if self._sqlite_backend == "aiosqlite":
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        else:
            rows = await asyncio.to_thread(cursor.fetchall)
            columns = [desc[0] for desc in cursor.description]

        hypotheses = []
        for row in rows:
            hyp = dict(zip(columns, row))
            hyp["result"] = json.loads(hyp.get("result", "{}"))
            hypotheses.append(hyp)

        return hypotheses

    async def save_finding(self, finding: dict[str, Any]) -> None:
        """Save a confirmed finding."""
        await self._execute(
            """
            INSERT OR REPLACE INTO findings
            (id, run_id, title, severity, status, vuln_type, target, description, evidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                finding.get("id"),
                self.run_id,
                finding.get("title"),
                finding.get("severity"),
                finding.get("status", "potential"),
                finding.get("vuln_type"),
                finding.get("target"),
                finding.get("description"),
                json.dumps(finding.get("evidence", [])),
                datetime.now().isoformat(),
            ),
        )
        await self._commit()

    async def get_findings(self, severity: str | None = None) -> list[dict[str, Any]]:
        """Get findings, optionally filtered by severity."""
        if severity:
            cursor = await self._execute(
                "SELECT * FROM findings WHERE run_id = ? AND severity = ?",
                (self.run_id, severity),
            )
        else:
            cursor = await self._execute(
                "SELECT * FROM findings WHERE run_id = ?",
                (self.run_id,),
            )

        if self._sqlite_backend == "aiosqlite":
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        else:
            rows = await asyncio.to_thread(cursor.fetchall)
            columns = [desc[0] for desc in cursor.description]

        findings = []
        for row in rows:
            finding = dict(zip(columns, row))
            finding["evidence"] = json.loads(finding.get("evidence", "[]"))
            findings.append(finding)

        return findings

    async def log_tool_call(
        self,
        tool: str,
        action: str,
        target: str,
        success: bool,
        duration_ms: float,
    ) -> None:
        """Log a tool invocation."""
        await self._execute(
            """
            INSERT INTO tool_calls (run_id, tool, action, target, success, duration_ms, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.run_id,
                tool,
                action,
                target,
                1 if success else 0,
                duration_ms,
                datetime.now().isoformat(),
            ),
        )
        await self._commit()

    async def export_to_json(self, output_dir: Path | None = None) -> dict[str, Path]:
        """Export all data to JSON files."""
        output_dir = output_dir or self.workspace_path

        exports = {}

        # Export assets
        assets = await self.get_assets()
        assets_file = output_dir / "recon" / "assets.json"
        assets_file.parent.mkdir(parents=True, exist_ok=True)
        with open(assets_file, "w") as f:
            json.dump(assets, f, indent=2)
        exports["assets"] = assets_file

        # Export hypotheses
        hypotheses = await self.get_hypotheses()
        hyp_file = output_dir / "hypotheses" / "hypotheses.json"
        hyp_file.parent.mkdir(parents=True, exist_ok=True)
        with open(hyp_file, "w") as f:
            json.dump(hypotheses, f, indent=2)
        exports["hypotheses"] = hyp_file

        # Export findings
        findings = await self.get_findings()
        findings_file = output_dir / "findings" / "findings.json"
        findings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(findings_file, "w") as f:
            json.dump(findings, f, indent=2)
        exports["findings"] = findings_file

        return exports

    async def export_run(self, output_dir: Path | None = None) -> Path:
        output_dir = output_dir or self.workspace_path
        await self.export_to_json(output_dir=output_dir)
        return output_dir

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            if self._sqlite_backend == "aiosqlite":
                await self._db.close()
            else:
                await asyncio.to_thread(self._db.close)


async def create_storage(run_context: RunContext) -> WorkspaceStorage:
    """Create and initialize storage for a run."""
    storage = WorkspaceStorage(run_context.workspace_path, run_context.run_id)
    await storage.initialize()
    return storage
