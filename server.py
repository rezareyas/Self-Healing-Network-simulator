"""NC-04 Self-Healing Network Simulator backend.

The simulator only uses synthetic telemetry. AI is advisory and never executes
network commands. Configure an OpenAI-compatible chat-completions endpoint via
environment variables; otherwise the transparent local rules remain available.
"""
from flask import Flask, jsonify, request, send_from_directory
import json
import os
import urllib.error
import urllib.request

app = Flask(__name__, static_folder=".", static_url_path="")


def ai_settings():
    base = os.getenv("AI_BASE_URL", "").strip().rstrip("/")
    key = os.getenv("AI_API_KEY", "").strip()
    model = os.getenv("AI_MODEL", "").strip()
    return base, key, model


def local_diagnosis(scenario, metrics):
    evidence = {
        "degradation": {
            "cause": "Primary link degradation / probable edge-link quality issue",
            "why": "The simulated primary route has high latency and packet loss; the backup route is marked healthy.",
            "action": "Recommend switching to backup route R2, then inspect the primary link.",
            "confidence": 92,
        },
        "failure": {
            "cause": "Primary edge link failure",
            "why": "The simulated primary route is down, with 100% packet loss and zero throughput; backup R2 is available.",
            "action": "Recommend failing over to backup route R2 and investigating the primary link.",
            "confidence": 99,
        },
        "congestion": {
            "cause": "Primary-path congestion",
            "why": "The simulated primary path has elevated latency and reduced throughput, consistent with congestion.",
            "action": "Recommend moving traffic to R2 if it is healthy and investigating primary-path load.",
            "confidence": 88,
        },
    }
    result = evidence.get(scenario, {
        "cause": "No known simulated fault pattern",
        "why": "The supplied scenario did not match a supported test case.",
        "action": "Collect more telemetry and verify route health before taking action.",
        "confidence": 50,
    }).copy()
    result["mode"] = "local_rule_based"
    result["model"] = None
    return result


def call_ai(scenario, metrics, fallback):
    base, key, model = ai_settings()
    if not (base and key and model):
        return fallback
    # Accept either a server base URL or a URL already ending in /chat/completions.
    endpoint = base if base.endswith("/chat/completions") else base + "/chat/completions"
    prompt = {
        "role": "user",
        "content": (
            "You are an advisory network troubleshooting assistant for a SIMULATOR. "
            "All supplied telemetry is synthetic. Do not claim to have changed a real network. "
            "Return ONLY valid JSON with keys cause, why, action, confidence. "
            "Keep each text field concise. confidence must be an integer from 0 to 100. "
            "Recommend actions only; never issue commands.\n"
            + json.dumps({"scenario": scenario, "synthetic_metrics": metrics, "rule_based_fallback": fallback}, ensure_ascii=False)
        ),
    }
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": "Diagnose simulated network incidents accurately and conservatively. Output JSON only."},
            prompt,
        ],
        "temperature": 0.2,
        "max_tokens": 250,
    }).encode("utf-8")
    req = urllib.request.Request(endpoint, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + key,
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=18) as response:
            data = json.loads(response.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        # Handle models that wrap JSON in a markdown fence.
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            if content.endswith("```"):
                content = content[:-3].strip()
        parsed = json.loads(content)
        confidence = max(0, min(100, int(parsed.get("confidence", fallback["confidence"]))))
        return {
            "cause": str(parsed.get("cause") or fallback["cause"])[:240],
            "why": str(parsed.get("why") or fallback["why"])[:500],
            "action": str(parsed.get("action") or fallback["action"])[:500],
            "confidence": confidence,
            "mode": "live_ai",
            "model": model,
        }
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError, TypeError, IndexError, json.JSONDecodeError):
        # Never break the demo if the optional provider is down or incompatible.
        return fallback


@app.get("/")
def home():
    return send_from_directory(".", "index.html")


@app.get("/api/status")
def status():
    base, key, model = ai_settings()
    configured = bool(base and key and model)
    return jsonify({
        "configured": configured,
        "mode": "live_ai_available" if configured else "local_rule_based",
        "model": model if configured else None,
        "message": "AI endpoint settings are present; connection is checked when a diagnosis is requested." if configured else "Using local rule-based diagnosis. Configure all three AI environment variables to enable optional AI.",
    })


@app.post("/api/diagnose")
def diagnose():
    body = request.get_json(silent=True) or {}
    scenario = str(body.get("scenario", "unknown"))[:40]
    metrics = body.get("metrics", {})
    if not isinstance(metrics, dict):
        metrics = {}
    fallback = local_diagnosis(scenario, metrics)
    return jsonify(call_ai(scenario, metrics, fallback))


if __name__ == "__main__":
    print("NC-04 Self-Healing Network Simulator")
    print("Open http://127.0.0.1:5000")
    print("Mode:", "optional AI configured" if ai_settings()[0] and ai_settings()[1] and ai_settings()[2] else "local rule-based (safe default)")
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
