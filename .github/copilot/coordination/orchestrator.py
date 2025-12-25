#!/usr/bin/env python3
"""
Parallel Agent Orchestrator for GitHub Copilot

This script orchestrates multiple GitHub Copilot agents working in parallel
on the same pull request, coordinating through a shared state file.
"""

import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class AgentCoordinator:
    """Coordinates multiple agents working on the same PR."""
    
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load coordination state from file."""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return self._create_initial_state()
    
    def _save_state(self):
        """Save coordination state to file."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _create_initial_state(self) -> Dict[str, Any]:
        """Create initial coordination state."""
        return {
            "pr_number": 117,
            "coordination_version": "1.0",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": "initialized",
            "agents": {},
            "tasks": {},
            "progress": {
                "total_tasks": 0,
                "completed_tasks": 0,
                "in_progress_tasks": 0,
                "pending_tasks": 0,
                "percentage_complete": 0
            },
            "communication": {
                "last_update": datetime.utcnow().isoformat() + "Z",
                "messages": []
            }
        }
    
    def register_agent(self, agent_id: str, depends_on: Optional[List[str]] = None):
        """Register a new agent in the coordination system."""
        self.state["agents"][agent_id] = {
            "status": "registered",
            "depends_on": depends_on or [],
            "tasks_claimed": [],
            "tasks_completed": [],
            "started_at": None,
            "completed_at": None,
            "outputs": {}
        }
        self._save_state()
    
    def register_task(self, task_id: str, priority: int = 5,
                     depends_on: Optional[List[str]] = None,
                     estimated_effort: str = "unknown"):
        """Register a new task in the coordination system."""
        self.state["tasks"][task_id] = {
            "status": "pending",
            "assigned_to": None,
            "priority": priority,
            "depends_on": depends_on or [],
            "estimated_effort": estimated_effort,
            "started_at": None,
            "completed_at": None
        }
        self.state["progress"]["total_tasks"] += 1
        self.state["progress"]["pending_tasks"] += 1
        self._save_state()
    
    def can_agent_start(self, agent_id: str) -> bool:
        """Check if an agent can start based on dependencies."""
        agent = self.state["agents"].get(agent_id)
        if not agent:
            return False
        
        # Check if all dependency agents have completed
        for dep_agent_id in agent.get("depends_on", []):
            dep_agent = self.state["agents"].get(dep_agent_id)
            if not dep_agent or dep_agent["status"] != "completed":
                return False
        
        return True
    
    def claim_task(self, agent_id: str, task_id: str) -> bool:
        """Attempt to claim a task for an agent."""
        task = self.state["tasks"].get(task_id)
        if not task or task["assigned_to"] is not None:
            return False
        
        # Check task dependencies
        for dep_task_id in task.get("depends_on", []):
            dep_task = self.state["tasks"].get(dep_task_id)
            if not dep_task or dep_task["status"] != "completed":
                return False
        
        # Claim the task
        task["assigned_to"] = agent_id
        task["status"] = "in_progress"
        task["started_at"] = datetime.utcnow().isoformat() + "Z"
        
        agent = self.state["agents"][agent_id]
        agent["tasks_claimed"].append(task_id)
        if agent["status"] == "registered":
            agent["status"] = "in_progress"
            agent["started_at"] = datetime.utcnow().isoformat() + "Z"
        
        self.state["progress"]["in_progress_tasks"] += 1
        self.state["progress"]["pending_tasks"] -= 1
        self._update_progress()
        self._save_state()
        
        return True
    
    def complete_task(self, agent_id: str, task_id: str, outputs: Optional[Dict] = None):
        """Mark a task as completed."""
        task = self.state["tasks"].get(task_id)
        if not task or task["assigned_to"] != agent_id:
            return False
        
        task["status"] = "completed"
        task["completed_at"] = datetime.utcnow().isoformat() + "Z"
        
        agent = self.state["agents"][agent_id]
        agent["tasks_completed"].append(task_id)
        if outputs:
            agent["outputs"].update(outputs)
        
        # Check if agent has completed all tasks
        if set(agent["tasks_claimed"]) == set(agent["tasks_completed"]):
            agent["status"] = "completed"
            agent["completed_at"] = datetime.utcnow().isoformat() + "Z"
        
        self.state["progress"]["completed_tasks"] += 1
        self.state["progress"]["in_progress_tasks"] -= 1
        self._update_progress()
        self._save_state()
        
        return True
    
    def _update_progress(self):
        """Update overall progress percentage."""
        total = self.state["progress"]["total_tasks"]
        if total > 0:
            completed = self.state["progress"]["completed_tasks"]
            self.state["progress"]["percentage_complete"] = int((completed / total) * 100)
    
    def add_message(self, from_agent: str, to_agent: Optional[str], message: str):
        """Add a communication message between agents."""
        self.state["communication"]["messages"].append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "from": from_agent,
            "to": to_agent or "all",
            "message": message
        })
        self.state["communication"]["last_update"] = datetime.utcnow().isoformat() + "Z"
        self._save_state()
    
    def get_messages_for_agent(self, agent_id: str) -> List[Dict]:
        """Get all messages for a specific agent."""
        messages = []
        for msg in self.state["communication"]["messages"]:
            if msg["to"] == agent_id or msg["to"] == "all":
                messages.append(msg)
        return messages
    
    def get_available_tasks(self, agent_id: str) -> List[str]:
        """Get list of tasks available for an agent to claim."""
        available = []
        for task_id, task in self.state["tasks"].items():
            if task["status"] == "pending":
                # Check dependencies
                deps_met = True
                for dep_task_id in task.get("depends_on", []):
                    dep_task = self.state["tasks"].get(dep_task_id)
                    if not dep_task or dep_task["status"] != "completed":
                        deps_met = False
                        break
                
                if deps_met:
                    available.append(task_id)
        
        # Sort by priority (higher priority first)
        available.sort(key=lambda tid: self.state["tasks"][tid]["priority"], reverse=True)
        return available
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of the current coordination state."""
        return {
            "pr_number": self.state["pr_number"],
            "overall_status": self.state["status"],
            "progress": self.state["progress"],
            "agents": {
                agent_id: {
                    "status": agent["status"],
                    "tasks_claimed": len(agent["tasks_claimed"]),
                    "tasks_completed": len(agent["tasks_completed"])
                }
                for agent_id, agent in self.state["agents"].items()
            },
            "pending_tasks": [
                task_id for task_id, task in self.state["tasks"].items()
                if task["status"] == "pending"
            ],
            "in_progress_tasks": [
                task_id for task_id, task in self.state["tasks"].items()
                if task["status"] == "in_progress"
            ]
        }
    
    def is_complete(self) -> bool:
        """Check if all tasks are completed."""
        return self.state["progress"]["completed_tasks"] == self.state["progress"]["total_tasks"]


def main():
    """Main entry point for the orchestrator."""
    parser = argparse.ArgumentParser(description="Coordinate parallel GitHub Copilot agents")
    parser.add_argument("--state-file", type=Path, required=True,
                       help="Path to coordination state file")
    parser.add_argument("--command", choices=["status", "init", "reset"],
                       default="status", help="Command to execute")
    parser.add_argument("--pr-number", type=int, default=117,
                       help="Pull request number")
    
    args = parser.parse_args()
    
    coordinator = AgentCoordinator(args.state_file)
    
    if args.command == "status":
        summary = coordinator.get_status_summary()
        print(json.dumps(summary, indent=2))
    
    elif args.command == "init":
        # Initialize for PR 117
        coordinator.register_agent("test_optimizer")
        coordinator.register_agent("code_reviewer", depends_on=["test_optimizer"])
        
        # Register tasks
        coordinator.register_task("test_threshold_network_patterns", priority=10, estimated_effort="30min")
        coordinator.register_task("test_immunefi_intelligence_integration", priority=10, estimated_effort="20min")
        coordinator.register_task("test_hypothesis_enhancement", priority=10, estimated_effort="25min")
        coordinator.register_task("test_cross_chain_vulnerability_detection", priority=10, estimated_effort="20min")
        
        coordinator.register_task("fix_mypy_type_errors", priority=8,
                                 depends_on=["test_threshold_network_patterns", "test_immunefi_intelligence_integration"],
                                 estimated_effort="40min")
        coordinator.register_task("fix_pylint_issues", priority=7, estimated_effort="30min")
        coordinator.register_task("optimize_complexity", priority=7, estimated_effort="35min")
        coordinator.register_task("review_security_patterns", priority=8, estimated_effort="25min")
        
        coordinator.state["status"] = "ready"
        coordinator._save_state()
        print(f"Initialized coordination for PR #{args.pr_number}")
    
    elif args.command == "reset":
        coordinator.state = coordinator._create_initial_state()
        coordinator._save_state()
        print("Reset coordination state")


if __name__ == "__main__":
    main()
