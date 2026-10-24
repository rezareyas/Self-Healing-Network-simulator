# NC-04 — Self-Healing Network Simulator (AI-Ready Enhanced Version)

## Improvements
- Dashboard calls the Python `/api/diagnose` endpoint for each simulated fault.
- Optional OpenAI-compatible language-model diagnosis.
- Clearly labels `LIVE AI RESPONSE` only when a model response succeeds; otherwise uses local rule-based fallback.
- Keeps API keys on the backend, never in browser JavaScript.
- Displays topology, latency, packet loss, throughput, network score, test incidents, workflow and event log.
- Model text is displayed as text, not interpreted as HTML.

## Important limitation
This is an educational **simulator**. Telemetry is synthetic and failover is visual only. It does not change Wi-Fi, routers, OS routes or real network traffic. AI recommendations are advisory and never executed as commands.

## Run on Windows
1. Install Python 3.10+.
2. Open PowerShell in this extracted folder.
3. Run:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server.py
```
4. Open http://127.0.0.1:5000 and keep PowerShell open. If `py` is unavailable, use `python`.

## Optional AI setup
Use only a provider whose official documentation confirms it supports OpenAI-compatible Chat Completions. Replace these placeholders with official provider details; do not share your API key:
```powershell
$env:AI_BASE_URL = "https://YOUR-TRUSTED-PROVIDER-BASE-URL/v1"
$env:AI_MODEL = "YOUR-EXACT-MODEL-NAME"
$env:AI_API_KEY = Read-Host "Paste API key"
python server.py
```
A configured URL alone does not prove the model is working. Trigger a fault and check for `LIVE AI RESPONSE`. `LOCAL RULE-BASED` means fallback was used.

## Viva description
“Our prototype uses synthetic telemetry to detect simulated incidents, diagnoses them using local rules or an optional language model, recommends a safe failover, and visually verifies simulated recovery. AI does not execute commands, and the demo does not modify a real network.”
