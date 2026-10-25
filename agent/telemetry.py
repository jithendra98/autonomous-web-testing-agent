"""
Diagnostic Artifact Generator & Telemetry Reporting
Aggregates execution traces, self-healing events, console errors, network failures,
and screenshots into an interactive HTML scorecard and structured JSON report.
"""

from typing import Dict, Any, List
import json
import os
from datetime import datetime


class TelemetryReporter:
    """
    Generates structured test reports and visual HTML audit dashboards.
    """

    @classmethod
    def generate_html_report(
        cls,
        scenario_name: str,
        status: str,
        steps: List[Dict[str, Any]],
        dom_metrics: Dict[str, Any],
        console_logs: List[Dict[str, Any]],
        failed_requests: List[Dict[str, Any]],
        screenshot_path: str,
        output_filepath: str
    ) -> str:
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

        status_color = "#10b981" if status.upper() == "PASSED" else "#ef4444"
        if status.upper() == "RECOVERED":
            status_color = "#f59e0b"

        steps_rows = ""
        for s in steps:
            tier_badge = ""
            if "recovery_tier" in s and s["recovery_tier"]:
                badge_color = "#22c55e" if "Tier 0" in s["recovery_tier"] else "#f59e0b"
                tier_badge = f'<span style="background:{badge_color};color:#000;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;">{s["recovery_tier"]}</span>'

            steps_rows += f"""
            <tr>
                <td style="padding:10px;border-bottom:1px solid #334155;">{s.get('step_num', '-')}</td>
                <td style="padding:10px;border-bottom:1px solid #334155;font-weight:600;color:#60a5fa;">{s.get('action', '')}</td>
                <td style="padding:10px;border-bottom:1px solid #334155;color:#e2e8f0;">{s.get('target', '')}</td>
                <td style="padding:10px;border-bottom:1px solid #334155;">{tier_badge}</td>
                <td style="padding:10px;border-bottom:1px solid #334155;color:#94a3b8;">{s.get('details', '')}</td>
            </tr>
            """

        console_rows = ""
        for c in console_logs:
            c_color = "#ef4444" if c.get("type") == "error" else "#f59e0b"
            console_rows += f"""<div style="font-family:monospace;color:{c_color};margin-bottom:4px;">[{c.get('type','').upper()}] {c.get('text','')}</div>"""
        if not console_rows:
            console_rows = '<div style="color:#94a3b8;font-style:italic;">No console errors detected.</div>'

        network_rows = ""
        for n in failed_requests:
            network_rows += f"""<div style="font-family:monospace;color:#ef4444;margin-bottom:4px;">[HTTP {n.get('status', 'ERR')}] {n.get('url','')}</div>"""
        if not network_rows:
            network_rows = '<div style="color:#94a3b8;font-style:italic;">No failed network requests (0 HTTP 4xx/5xx).</div>'

        rel_screenshot = os.path.basename(screenshot_path) if screenshot_path else ""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Autonomous Agent Test Diagnostic - {scenario_name}</title>
    <style>
        body {{
            background-color: #0f172a;
            color: #f8fafc;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 30px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #1e293b;
            padding-bottom: 16px;
        }}
        .badge {{
            background: {status_color};
            color: #fff;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
        }}
        .cards {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin: 24px 0;
        }}
        .card {{
            background: #1e293b;
            border-radius: 8px;
            padding: 16px;
            border-left: 4px solid #3b82f6;
        }}
        .card h4 {{ margin: 0 0 8px 0; color: #94a3b8; font-size: 12px; text-transform: uppercase; }}
        .card .val {{ font-size: 22px; font-weight: bold; color: #f1f5f9; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #1e293b;
            border-radius: 8px;
            overflow: hidden;
            margin-top: 16px;
        }}
        th {{
            background: #334155;
            color: #cbd5e1;
            padding: 12px;
            text-align: left;
            font-size: 13px;
        }}
        .section {{ margin-top: 30px; }}
        .section-title {{ font-size: 18px; font-weight: bold; margin-bottom: 12px; color: #38bdf8; }}
        .terminal-box {{
            background: #020617;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 14px;
            font-size: 13px;
            max-height: 200px;
            overflow-y: auto;
        }}
        .screenshot-img {{
            max-width: 100%;
            border-radius: 8px;
            border: 1px solid #334155;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1 style="margin:0;font-size:24px;">Autonomous Web Testing & DOM Exploration Agent</h1>
            <p style="margin:4px 0 0;color:#94a3b8;">Scenario: <strong>{scenario_name}</strong> | Executed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        <div class="badge">{status.upper()}</div>
    </div>

    <div class="cards">
        <div class="card" style="border-left-color:#38bdf8;">
            <h4>Raw HTML Size</h4>
            <div class="val">{dom_metrics.get('raw_html_chars', 0):,} chars</div>
        </div>
        <div class="card" style="border-left-color:#10b981;">
            <h4>Semantic DOM Pruned</h4>
            <div class="val">{dom_metrics.get('pruned_chars', 0):,} chars</div>
        </div>
        <div class="card" style="border-left-color:#a855f7;">
            <h4>Token Savings</h4>
            <div class="val">{dom_metrics.get('token_savings_percent', 0)}% Cut</div>
        </div>
        <div class="card" style="border-left-color:#f59e0b;">
            <h4>Interactive Elements</h4>
            <div class="val">{dom_metrics.get('interactive_elements_count', 0)} nodes</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Step-by-Step Autonomous Action & Recovery Trace</div>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Action</th>
                    <th>Target / Selector</th>
                    <th>Self-Healing Tier</th>
                    <th>Details & Diagnostics</th>
                </tr>
            </thead>
            <tbody>
                {steps_rows}
            </tbody>
        </table>
    </div>

    <div class="section" style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
        <div>
            <div class="section-title">Console Error Stream Interception</div>
            <div class="terminal-box">{console_rows}</div>
        </div>
        <div>
            <div class="section-title">Failed HTTP Requests & Network Telemetry</div>
            <div class="terminal-box">{network_rows}</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Final Execution Artifact Screenshot</div>
        <div>
            <img src="{rel_screenshot}" alt="Execution Screenshot" class="screenshot-img" />
        </div>
    </div>
</body>
</html>"""

        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(html)

        # Also write structured JSON
        json_path = output_filepath.replace(".html", ".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "scenario": scenario_name,
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "dom_metrics": dom_metrics,
                "steps": steps,
                "console_errors": len([c for c in console_logs if c.get('type') == 'error']),
                "failed_network_requests": len(failed_requests),
                "screenshot": screenshot_path
            }, f, indent=2)

        return output_filepath
