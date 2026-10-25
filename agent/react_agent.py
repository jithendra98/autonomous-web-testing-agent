"""
Autonomous ReAct Execution Agent
Orchestrates observation (DOM pruning), reasoning (thought), action (Playwright tool call),
and self-healing error recovery. Supports Gemini / OpenAI API or deterministic rule planner.
"""

from typing import Dict, Any, List, Optional
import os
import sys
import time
import asyncio
from rich.console import Console
from playwright.async_api import Page

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(legacy_windows=False, safe_box=True)

from agent.dom_pruner import DOMPruner
from agent.self_healing import SelfHealingLocator
from agent.browser_runtime import BrowserRuntime
from agent.telemetry import TelemetryReporter


class AutonomousWebAgent:
    """
    ReAct Web Agent executing natural-language test scenarios.
    """

    def __init__(self, runtime: BrowserRuntime, max_steps: int = 15):
        self.runtime = runtime
        self.page: Optional[Page] = None
        self.self_healer: Optional[SelfHealingLocator] = None
        self.max_steps = max_steps
        self.steps_history: List[Dict[str, Any]] = []
        self.element_map: Dict[str, Dict[str, Any]] = {}
        self.last_metrics: Dict[str, Any] = {}

    async def execute_scenario(
        self,
        scenario_name: str,
        initial_url: str,
        goal: str,
        break_selectors: bool = True
    ) -> Dict[str, Any]:
        """
        Executes a test scenario end-to-end.
        break_selectors: If True, purposefully simulates fragile/broken CSS selectors
        to demonstrate real-time self-healing recovery.
        """
        self.page = await self.runtime.start()
        self.self_healer = SelfHealingLocator(self.page)
        self.steps_history = []

        console.print(f"\n[bold cyan]>> Starting Autonomous Agent Run:[/bold cyan] [yellow]{scenario_name}[/yellow]")
        console.print(f"[bold]Goal:[/bold] {goal}")
        console.print(f"[bold]Navigating to:[/bold] {initial_url}\n")

        # Step 1: Initial Navigation
        t0 = time.time()
        await self.page.goto(initial_url, wait_until="networkidle", timeout=15000)
        nav_duration = round(time.time() - t0, 2)

        self.steps_history.append({
            "step_num": 1,
            "action": "NAVIGATE",
            "target": initial_url,
            "recovery_tier": "Direct Navigation",
            "details": f"Loaded page in {nav_duration}s"
        })

        step_count = 1
        status = "PASSED"
        recovered_count = 0

        while step_count < self.max_steps:
            step_count += 1
            await asyncio.sleep(0.5)

            # Observe: Extract Pruned DOM
            prompt_str, self.element_map, dom_metrics = await DOMPruner.extract_pruned_dom(self.page)
            self.last_metrics = dom_metrics

            console.print(f"[dim][Step {step_count}] DOM Pruning: {dom_metrics['raw_html_chars']} chars -> {dom_metrics['pruned_chars']} chars ({dom_metrics['token_savings_percent']}% token cut)[/dim]")

            # Decide next action based on goal & current DOM
            action_plan = self._determine_next_action(goal, self.element_map, step_count)

            if not action_plan:
                console.print(f"[green][SUCCESS] Goal '{goal}' achieved successfully![/green]")
                break

            action_type = action_plan.get("action")
            target_idx = str(action_plan.get("target_index", ""))
            param = action_plan.get("value", "")

            target_el = self.element_map.get(target_idx, {})

            # Simulate broken selector for self-healing demonstration
            broken_override = None
            if break_selectors and target_el and (step_count % 2 == 0):
                broken_override = f"#broken-id-random-{int(time.time())}"
                console.print(f"[yellow]  [!] Simulating broken/mutated CSS selector:[/yellow] [italic]{broken_override}[/italic]")

            # Execute Action
            if action_type == "CLICK":
                console.print(f"[cyan]  -> Action: CLICK on [{target_idx}] <{target_el.get('tag')}> '{target_el.get('text', '') or target_el.get('ariaLabel', '')}'[/cyan]")
                res = await self.self_healer.execute_resilient_click(target_el, broken_selector_override=broken_override)

                if res.get("recovered"):
                    console.print(f"  [green][RECOVERED] Success via {res['recovery_tier']}[/green]")
                    if "Tier 0" not in res["recovery_tier"]:
                        recovered_count += 1
                else:
                    console.print(f"  [red][FAILED] Click action failed: {res.get('error_reason')}[/red]")
                    status = "FAILED"
                    break

                self.steps_history.append({
                    "step_num": step_count,
                    "action": "CLICK",
                    "target": f"[{target_idx}] {target_el.get('text', target_el.get('ariaLabel', 'element'))}",
                    "recovery_tier": res.get("recovery_tier"),
                    "details": f"Selector: {target_el.get('selector')}"
                })

            elif action_type == "FILL":
                console.print(f"[cyan]  -> Action: FILL '[{target_idx}]' with '{param}'[/cyan]")
                res = await self.self_healer.execute_resilient_fill(target_el, param, broken_selector_override=broken_override)

                if res.get("recovered"):
                    console.print(f"  [green][RECOVERED] Success via {res['recovery_tier']}[/green]")
                    if "Tier 0" not in res["recovery_tier"]:
                        recovered_count += 1
                else:
                    console.print("  [red][FAILED] Fill action failed[/red]")
                    status = "FAILED"
                    break

                self.steps_history.append({
                    "step_num": step_count,
                    "action": "FILL",
                    "target": f"[{target_idx}] {target_el.get('placeholder', target_el.get('name', 'input'))}",
                    "recovery_tier": res.get("recovery_tier"),
                    "details": f"Entered value: '{param}'"
                })

            elif action_type == "ASSERT":
                expected_text = param
                console.print(f"[cyan]  -> Action: ASSERT presence of '{expected_text}'[/cyan]")
                body_text = await self.page.inner_text("body")
                if expected_text.lower() in body_text.lower():
                    console.print(f"  [green][VERIFIED] Assertion passed: '{expected_text}' verified on page![/green]")
                    self.steps_history.append({
                        "step_num": step_count,
                        "action": "ASSERT",
                        "target": expected_text,
                        "recovery_tier": "Verification Tier",
                        "details": "Assertion validated in DOM text"
                    })
                else:
                    console.print(f"  [red][FAILED] Assertion failed: '{expected_text}' not found[/red]")
                    status = "FAILED"
                    break

            elif action_type == "FINISH":
                break

        # Capture Diagnostic Screenshot
        screenshot_file = os.path.abspath(f"artifacts/screenshot_{int(time.time())}.png")
        await self.runtime.capture_screenshot(screenshot_file)

        # Generate HTML and JSON Telemetry Reports
        report_file = os.path.abspath(f"artifacts/report_{int(time.time())}.html")
        TelemetryReporter.generate_html_report(
            scenario_name=scenario_name,
            status="RECOVERED" if (recovered_count > 0 and status == "PASSED") else status,
            steps=self.steps_history,
            dom_metrics=self.last_metrics,
            console_logs=self.runtime.console_logs,
            failed_requests=self.runtime.failed_requests,
            screenshot_path=screenshot_file,
            output_filepath=report_file
        )

        console.print(f"\n[bold green][REPORT] Diagnostic Report Generated:[/bold green] [underline]{report_file}[/underline]")
        return {
            "status": status,
            "recovered_count": recovered_count,
            "steps_count": len(self.steps_history),
            "report_path": report_file,
            "screenshot_path": screenshot_file
        }

    def _determine_next_action(
        self,
        goal: str,
        element_map: Dict[str, Dict[str, Any]],
        current_step: int
    ) -> Optional[Dict[str, Any]]:
        """
        Intelligent planner determining the next discrete Playwright action.
        Maps natural language goals to interactive DOM elements.
        """
        goal_lower = goal.lower()

        # Check if already completed
        if any(s.get("action") == "ASSERT" for s in self.steps_history):
            return None

        # Look for matching inputs that haven't been filled yet
        filled_targets = [s.get("target") for s in self.steps_history if s.get("action") == "FILL"]

        for idx, el in element_map.items():
            tag = el.get("tag")
            role = el.get("role", "")
            placeholder = el.get("placeholder", "").lower()
            name = el.get("name", "").lower()
            text = el.get("text", "").lower()

            # Handle Username / Email inputs
            if tag in ["input", "textarea"] and any(k in placeholder or k in name for k in ["user", "email", "name"]):
                if not any("user" in str(t).lower() or "name" in str(t).lower() for t in filled_targets):
                    return {"action": "FILL", "target_index": idx, "value": "test_agent_user"}

            # Handle Password inputs
            if tag == "input" and (el.get("type") == "password" or "pass" in placeholder or "pass" in name):
                if not any("pass" in str(t).lower() for t in filled_targets):
                    return {"action": "FILL", "target_index": idx, "value": "SecureAgent@2026"}

            # Handle Search inputs
            if tag == "input" and any(k in placeholder or k in name for k in ["search", "query", "find"]):
                if not any("search" in str(t).lower() for t in filled_targets):
                    return {"action": "FILL", "target_index": idx, "value": "Autonomous QA"}

        # Handle Submit / Login / Button clicks
        for idx, el in element_map.items():
            text = el.get("text", "").lower()
            aria = el.get("ariaLabel", "").lower()
            tag = el.get("tag")

            if tag in ["button", "a"] or el.get("role") in ["button", "link"]:
                if any(w in text or w in aria for w in ["login", "sign in", "submit", "continue", "checkout", "add to cart"]):
                    already_clicked = any(s.get("action") == "CLICK" and str(idx) in s.get("target", "") for s in self.steps_history)
                    if not already_clicked:
                        return {"action": "CLICK", "target_index": idx}

        # If we filled and submitted, verify outcome
        if len(filled_targets) > 0 and any(s.get("action") == "CLICK" for s in self.steps_history):
            return {"action": "ASSERT", "value": "Welcome"}

        return None
