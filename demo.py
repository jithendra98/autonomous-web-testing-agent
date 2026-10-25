"""
Master Live Demonstration Script
Runs the Autonomous Web Testing & DOM Exploration Agent in headed browser mode,
demonstrates real-time Self-Healing recovery, generates diagnostic artifacts, and displays reports.
"""

import sys
import os
import asyncio
import threading
import time
import webbrowser
from rich.console import Console
from rich.panel import Panel

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(legacy_windows=False, safe_box=True)

from test_bench.app import run_server, PORT
from agent.browser_runtime import BrowserRuntime
from agent.react_agent import AutonomousWebAgent


def start_testbench_server():
    """Runs zero-dependency local test bench server on port 8000 in background thread."""
    try:
        run_server(PORT)
    except Exception:
        pass


async def run_live_demo(target_url: str = f"http://127.0.0.1:{PORT}"):
    console.print(Panel.fit(
        "[bold cyan]AUTONOMOUS WEB TESTING & DOM EXPLORATION AGENT[/bold cyan]\n"
        "[dim]Candidate Project Demo | OyeSense AI Agent Developer[/dim]\n\n"
        "[green]* Asynchronous ReAct Execution Loop[/green]\n"
        "[green]* Semantic DOM Pruning (65%+ Token Savings)[/green]\n"
        "[green]* 4-Tier Self-Healing Locator Fallbacks[/green]\n"
        "[green]* Diagnostic Telemetry (HAR + Console + Screenshots)[/green]",
        title="Project Demonstration",
        border_style="cyan",
        safe_box=True
    ))

    # Initialize Headed Browser Runtime for Live Screen Sharing
    runtime = BrowserRuntime(headless=False, slow_mo=450)
    agent = AutonomousWebAgent(runtime=runtime, max_steps=10)

    try:
        res = await agent.execute_scenario(
            scenario_name="E2E Portal Authentication & Resilient Recovery",
            initial_url=target_url,
            goal="Sign in with credentials and verify dashboard state",
            break_selectors=True  # Demonstrates self-healing when CSS breaks
        )

        console.print(Panel(
            f"[bold green]Status:[/bold green] {res['status']}\n"
            f"[bold yellow]Self-Healed Fallbacks:[/bold yellow] {res['recovered_count']} actions\n"
            f"[bold blue]Execution Steps:[/bold blue] {res['steps_count']}\n"
            f"[bold magenta]Diagnostic HTML Report:[/bold magenta] {res['report_path']}\n"
            f"[bold cyan]Screenshot Captured:[/bold cyan] {res['screenshot_path']}",
            title="Execution Summary",
            border_style="green",
            safe_box=True
        ))

        # Open the generated diagnostic report in browser
        time.sleep(1)
        webbrowser.open(f"file://{res['report_path']}")

    finally:
        await asyncio.sleep(2)
        await runtime.close()


def main():
    target_url = sys.argv[1] if len(sys.argv) > 1 else f"http://127.0.0.1:{PORT}"

    # Start local test bench if default URL
    if "127.0.0.1" in target_url or "localhost" in target_url:
        console.print(f"[dim]Starting local test bench on http://127.0.0.1:{PORT}...[/dim]")
        server_thread = threading.Thread(target=start_testbench_server, daemon=True)
        server_thread.start()
        time.sleep(0.5)

    asyncio.run(run_live_demo(target_url))


if __name__ == "__main__":
    main()
