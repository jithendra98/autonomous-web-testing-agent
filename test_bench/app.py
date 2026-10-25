"""
Zero-Dependency Local Test Bench Application for Autonomous Agent Demonstration
Uses Python standard library http.server (no external dependencies required).
Features dynamic/mutating CSS classes, realistic authentication flow, console log streams,
and intentional edge-case error injections for agent telemetry.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import time

PORT = 8000

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>OyeSense Test Portal - Autonomous QA Verification</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0f172a;
            color: #f8fafc;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }}
        .card {{
            background: #1e293b;
            border: 1px solid #334155;
            padding: 32px;
            border-radius: 12px;
            width: 380px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
        }}
        h2 {{ margin-top: 0; color: #38bdf8; text-align: center; }}
        .form-group {{ margin-bottom: 16px; }}
        label {{ display: block; margin-bottom: 6px; font-size: 13px; color: #94a3b8; }}
        input {{
            width: 100%;
            box-sizing: border-box;
            padding: 10px 14px;
            background: #0f172a;
            border: 1px solid #475569;
            border-radius: 6px;
            color: #fff;
            font-size: 14px;
        }}
        .btn-submit-{hash_suffix} {{
            width: 100%;
            background: #0284c7;
            color: #fff;
            border: none;
            padding: 12px;
            border-radius: 6px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .btn-submit-{hash_suffix}:hover {{
            background: #0369a1;
        }}
        .notice {{
            margin-top: 16px;
            font-size: 11px;
            color: #64748b;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h2>OyeSense QA Portal</h2>
        <p style="font-size: 13px; color: #94a3b8; text-align: center; margin-bottom: 24px;">
            Autonomous Agent Verification Benchmark
        </p>

        <form id="loginForm" onsubmit="event.preventDefault(); handleSubmit();">
            <div class="form-group">
                <label for="username">Username / Email</label>
                <input 
                    type="text" 
                    id="username" 
                    name="username" 
                    placeholder="Enter your username" 
                    aria-label="Username or Email"
                    required 
                />
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input 
                    type="password" 
                    id="password" 
                    name="password" 
                    placeholder="Enter your password" 
                    aria-label="Account Password"
                    required 
                />
            </div>
            <button 
                type="submit" 
                id="submitBtn"
                class="btn-submit-{hash_suffix}" 
                aria-label="Login to account"
            >
                Sign In to Dashboard
            </button>
        </form>

        <div id="statusMessage" style="display:none; margin-top:20px; padding:12px; background:#064e3b; border:1px solid #10b981; border-radius:6px; color:#a7f3d0; text-align:center;">
            <strong>Welcome, test_agent_user!</strong><br>
            <span>Authentication Assertion Verified.</span>
        </div>

        <div class="notice">
            Dynamic Class: <code>.btn-submit-{hash_suffix}</code>
        </div>
    </div>

    <script>
        console.log("[Portal] DOM fully initialized. Dynamic CSS token active.");
        console.warn("[Telemetry] Deprecated cookie session detected. Upgrading to JWT.");

        function handleSubmit() {{
            const user = document.getElementById('username').value;
            console.log("[Auth] Form submission triggered for user: " + user);
            document.getElementById('loginForm').style.display = 'none';
            document.getElementById('statusMessage').style.display = 'block';
        }}
    </script>
</body>
</html>"""


class TestBenchHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence default server access logs to keep terminal clean
        return

    def do_GET(self):
        hash_suffix = hex(int(time.time() * 1000))[-6:]
        html = HTML_TEMPLATE.format(hash_suffix=hash_suffix)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


def run_server(port=PORT):
    server = HTTPServer(("127.0.0.1", port), TestBenchHandler)
    server.serve_forever()


if __name__ == "__main__":
    print(f"Starting test bench server on http://127.0.0.1:{PORT}")
    run_server()
