"""
Cubiczan-MoE-7B Inference Server
================================
A structured strategic reasoning model powered by 20 domain-specialized expert frameworks.
Uses Gemini as the base model with comprehensive system prompt engineering to replicate
the Cubiczan MoE architecture's behavior.

Usage:
    python cubiczan_server.py                    # Start API server on port 8000
    python cubiczan_server.py --test             # Run a test query
    python cubiczan_server.py --interactive      # Interactive chat mode
"""

import os
import sys
import json
import argparse
from typing import Optional
from urllib.request import Request, urlopen

from critical_minerals_monitor import generate_critical_minerals_context
from investor_relations_engine import generate_investor_relations_package
from market_data_clients import fetch_market_context
from veris_simulation_engine import build_veris_briefing, build_veris_memory_packet, run_veris_simulation

# --- Configuration ---
INFERENCE_BACKEND = os.environ.get("CUBICZAN_INFERENCE_BACKEND", "openai").strip().lower()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.2")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# --- Cubiczan System Prompt (encodes all 20 expert frameworks) ---
CUBICZAN_SYSTEM_PROMPT = """You are Cubiczan-MoE-7B, a structured strategic reasoning model with 20 domain-specialized expert modules. You NEVER produce free-form prose for analytical queries. You ALWAYS:

1. IDENTIFY the appropriate expert(s) and framework(s)
2. DECLARE your routing with <|expert_route|> tags
3. PRODUCE structured output within <|framework_start|> and <|framework_end|> tags
4. USE tables, scoring matrices, decision trees, and templates -- not paragraphs

## YOUR 20 EXPERT MODULES

### Strategy Experts
- **E01 OKR Architecture** (Doerr): Objective-Key Result cascades, 0.0-1.0 scoring, committed vs aspirational, quarterly cadence
- **E02 Competitive Strategy** (Lafley-Martin "Playing to Win"): Five-choice cascade (Aspiration > Where to Play > How to Win > Capabilities > Systems), Cost Leadership OR Differentiation
- **E03 Market Creation** (Blue Ocean): ERRC grids (Eliminate/Reduce/Raise/Create), buyer utility maps (6 stages x 5 levers), non-customer tiers (1/2/3), strategy canvas
- **E04 Strategy Kernel** (Rumelt): Diagnosis > Guiding Policy > Coherent Actions. Detect bad strategy: fluff, goals-as-strategy, wish lists
- **E05 Lean Validation** (Ries): Value/Growth hypotheses, MVP types (smoke test > concierge > wizard-of-oz > single-feature), Build-Measure-Learn, pivot types (10 types)

### Decision-Making Experts
- **E06 Probabilistic Forecasting** (Tetlock): Decompose > outside view (base rate) > inside view (adjust) > synthesize. Use full probability range. Update triggers.
- **E07 Cognitive Debiasing** (Kahneman): System 1/2 errors. Tier 1: Anchoring, Overconfidence, Planning Fallacy, Confirmation, Availability. Tier 2: Loss Aversion, Sunk Cost, Framing, Representativeness, Status Quo. Output: RED/YELLOW/GREEN per bias.
- **E08 Decision Audit** (Heath WRAP): Widen options (vanishing options test, multi-track), Reality-test (zoom in/out, disconfirming), Attain distance (10/10/10 test, successor test), Prepare wrong (bookend futures, tripwires). Detect 4 villains.
- **E09 Probabilistic Betting** (Duke): Separate decision quality from outcome quality. Detect resulting. Calibrate confidence.

### Risk & Finance Experts
- **E10 Financial Risk** (5x5 Matrix): Probability (1-5) x Impact (1-5). Categories: Market/Credit/Liquidity/Operational/Strategic. Levels: Critical (20-25), High (12-19), Medium (6-11), Low (1-5). Responses: Avoid/Mitigate/Transfer/Accept.
- **E11 Investment Evaluation** (CFO Rubric): 5 weighted categories: Strategic Alignment (25%), Financial Return (30%), Execution Capability (20%), Risk Profile (15%), Stakeholder Impact (10%). Score 1-5. Thresholds: 90+=Strongly Recommended, 75-89=Recommended, 60-74=Conditional, <60=Not Recommended.
- **E12 Bottleneck Optimization** (Goldratt TOC): Five Focusing Steps: IDENTIFY > EXPLOIT > SUBORDINATE > ELEVATE > REPEAT. Drum-Buffer-Rope. Throughput Accounting (T > I > OE).
- **E13 Financial Narrative** (Storytelling): Context > Numbers > Implication > Action (CNIA). Numbers alone don't convince.
- **E14 Board Reporting** (Executive Reports): KPI dashboards with RED/YELLOW/GREEN status, executive summary, strategic updates, risks, decisions required.

### Innovation & Design Experts
- **E15 Design Thinking** (IDEO/d.school): Empathize > Define > Ideate > Prototype > Test. Empathy maps, journey maps, How Might We, Crazy 8s.

### AI & Agent Experts
- **E16 Agent Context Engineering**: AI agent behavior shaping, context window optimization
- **E17 Context Optimization**: Signal-to-noise maximization, prompt design patterns
- **E18 Multi-Agent Coordination** (Cognitive Mesh): Agent mesh topology, consensus mechanisms

### Cross-Domain Experts
- **E19 Cross-Domain Bridging**: Paradigm translation, cross-domain pattern matching
- **E20 First Principles** (MIT Method): Strip all assumptions > identify fundamental truths > recombine into novel solutions

## PROBLEM-SOLVING FRAMEWORKS (20 total)
For operational/diagnostic problems, also apply these frameworks:
- Root cause unclear: Cause-and-Effect Map, Root Cause 5 Whys, MECE Issue Tree
- Comparing options: Weighted Decision Grid, Cost-Benefit Scorecard, Counterfactual Lens
- Planning change: Force-Field Dynamics, Pre-Mortem Run, OODA Cycle
- Generating ideas: SCAMPER Remix, Lateral Shift, Analogy Lift, Blue-Ocean Canvas
- Validating assumptions: Hypothesis Test Plan, First-Principles Teardown, Inversion Drill
- Multi-stakeholder: Six Hats Roundtable, SWOT+ Reality Check
- Technical: TRIZ Pattern Pull, Prototype Sprint

## ROUTING RULES
- For any query, select the 1-3 most relevant experts
- Output your routing as: <|expert_route|> E##: Name (Framework) [+ additional if multi-expert]
- If multiple experts, execute in logical order (e.g., diagnose before evaluate)
- For strategic decisions, default to: Pre-Mortem + Counterfactual Lens + Weighted Decision Grid
- For operational problems, default to: Root Cause 5 Whys + MECE Issue Tree + Force-Field Dynamics

## OUTPUT FORMAT
Always use structured output: tables, scoring matrices, bullet trees, templates. Never write essay-style prose for analytical outputs. Every output must be actionable and specific."""


def _extract_openai_output_text(payload: dict) -> str:
    output_text = payload.get("output_text")
    if output_text:
        return output_text

    parts = []
    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                parts.append(content.get("text", ""))
    return "\n".join(part for part in parts if part).strip()


def get_openai_response(user_message: str, model_name: Optional[str] = None) -> str:
    """Call the OpenAI Responses API with the Cubiczan system prompt."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured.")

    request_body = {
        "model": model_name or OPENAI_MODEL,
        "instructions": CUBICZAN_SYSTEM_PROMPT,
        "input": user_message,
    }
    request = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=120) as response:
        payload = json.loads(response.read().decode("utf-8"))

    output_text = _extract_openai_output_text(payload)
    if not output_text:
        raise ValueError("OpenAI response did not include text output.")
    return output_text


def get_gemini_response(user_message: str, model_name: Optional[str] = None) -> str:
    """Call Gemini API with Cubiczan system prompt."""
    import google.generativeai as genai

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured.")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=model_name or GEMINI_MODEL,
        system_instruction=CUBICZAN_SYSTEM_PROMPT
    )

    response = model.generate_content(
        user_message,
        generation_config=genai.GenerationConfig(
            temperature=0.1,
            top_p=0.9,
            top_k=40,
            max_output_tokens=8192,
        )
    )
    return response.text


def get_model_response(user_message: str, model_name: Optional[str] = None, backend: Optional[str] = None) -> str:
    selected_backend = (backend or INFERENCE_BACKEND).strip().lower()
    if selected_backend == "openai":
        return get_openai_response(user_message, model_name=model_name)
    if selected_backend == "gemini":
        return get_gemini_response(user_message, model_name=model_name)
    raise ValueError(f"Unsupported inference backend: {selected_backend}")


def run_test():
    """Run a test query to verify Cubiczan is working."""
    test_queries = [
        "We're considering acquiring a competitor for $10M. Our revenue is $5M/year. Evaluate this decision.",
        "Our customer churn increased 40% this quarter. Help me understand why.",
        "Set Q3 OKRs for our engineering team focused on platform reliability.",
    ]

    print("=" * 80)
    print("CUBICZAN-MoE-7B TEST RUN")
    print("=" * 80)

    query = test_queries[0]
    print(f"\nQuery: {query}\n")
    print("-" * 80)

    response = get_model_response(query)
    print(response)
    print("-" * 80)
    print("\nTest complete.")


def run_interactive():
    """Interactive chat mode."""
    print("=" * 80)
    print("CUBICZAN-MoE-7B Interactive Mode")
    print("Type 'quit' to exit")
    print("=" * 80)

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ('quit', 'exit', 'q'):
                print("Goodbye.")
                break
            if not user_input:
                continue

            print("\nCubiczan: ", end="", flush=True)
            response = get_model_response(user_input)
            print(response)

        except KeyboardInterrupt:
            print("\nGoodbye.")
            break
        except Exception as e:
            print(f"\nError: {e}")


def run_server(port: int = 8000):
    """Run as HTTP API server."""
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
    except ImportError:
        print("HTTP server not available")
        return

    class CubiczanHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path == "/v1/chat/completions":
                content_length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(content_length))

                messages = body.get("messages", [])
                request_backend = body.get("backend")
                request_model = body.get("model")
                user_msg = ""
                for msg in messages:
                    if msg["role"] == "user":
                        user_msg = msg["content"]

                if not user_msg:
                    self.send_error(400, "No user message found")
                    return

                try:
                    response_text = get_model_response(
                        user_msg,
                        model_name=request_model,
                        backend=request_backend,
                    )
                    result = {
                        "id": "cubiczan-resp",
                        "model": request_model or (OPENAI_MODEL if (request_backend or INFERENCE_BACKEND).strip().lower() == "openai" else GEMINI_MODEL),
                        "backend": (request_backend or INFERENCE_BACKEND).strip().lower(),
                        "choices": [{
                            "message": {
                                "role": "assistant",
                                "content": response_text
                            }
                        }]
                    }
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
                except Exception as e:
                    self.send_error(500, str(e))
            elif self.path == "/v1/investor-relations/generate":
                content_length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(content_length))

                try:
                    external_config = body.get("external_data", {})
                    if external_config.get("enabled"):
                        body["market_context"] = fetch_market_context(
                            company_symbol=external_config.get("company_symbol"),
                            benchmark_symbol=external_config.get("benchmark_symbol", "SPY"),
                            sector=external_config.get("sector") or body.get("company", {}).get("sector"),
                            fred_series=external_config.get("fred_series"),
                        )
                    result = generate_investor_relations_package(body)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(result, indent=2).encode())
                except Exception as e:
                    self.send_error(500, str(e))
            elif self.path == "/v1/investor-relations/market-context":
                content_length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(content_length))

                try:
                    result = fetch_market_context(
                        company_symbol=body.get("company_symbol"),
                        benchmark_symbol=body.get("benchmark_symbol", "SPY"),
                        sector=body.get("sector"),
                        fred_series=body.get("fred_series"),
                    )
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(result, indent=2).encode())
                except Exception as e:
                    self.send_error(500, str(e))
            elif self.path == "/v1/critical-minerals/context":
                content_length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(content_length))

                try:
                    result = generate_critical_minerals_context(body)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(result, indent=2).encode())
                except Exception as e:
                    self.send_error(500, str(e))
            elif self.path == "/v1/veris/simulate":
                content_length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(content_length))

                try:
                    result = run_veris_simulation(body)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(result, indent=2).encode())
                except Exception as e:
                    self.send_error(500, str(e))
            elif self.path == "/v1/veris/briefing":
                content_length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(content_length))

                try:
                    result = build_veris_briefing(body)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(result, indent=2).encode())
                except Exception as e:
                    self.send_error(500, str(e))
            elif self.path == "/v1/veris/export":
                content_length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(content_length))

                try:
                    result = build_veris_memory_packet(body)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(result, indent=2).encode())
                except Exception as e:
                    self.send_error(500, str(e))
            else:
                self.send_error(404)

        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "healthy", "model": "cubiczan-moe-7b-v1"}).encode())
            elif self.path == "/v1/investor-relations/sample":
                sample_path = os.path.join(os.path.dirname(__file__), "sample_investor_relations_request.json")
                with open(sample_path, "r", encoding="utf-8") as sample_file:
                    sample_payload = json.load(sample_file)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(sample_payload, indent=2).encode())
            elif self.path == "/v1/critical-minerals/sample":
                sample_path = os.path.join(os.path.dirname(__file__), "sample_critical_minerals_request.json")
                with open(sample_path, "r", encoding="utf-8") as sample_file:
                    sample_payload = json.load(sample_file)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(sample_payload, indent=2).encode())
            elif self.path == "/v1/veris/sample":
                sample_path = os.path.join(os.path.dirname(__file__), "sample_veris_simulation_request.json")
                with open(sample_path, "r", encoding="utf-8") as sample_file:
                    sample_payload = json.load(sample_file)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(sample_payload, indent=2).encode())
            else:
                self.send_error(404)

        def log_message(self, format, *args):
            pass  # Suppress logs

    server = HTTPServer(("0.0.0.0", port), CubiczanHandler)
    print(f"Cubiczan API server running on http://localhost:{port}")
    print(f"  Default inference backend: {INFERENCE_BACKEND}")
    print(f"  POST /v1/chat/completions  - Send queries")
    print(f"  POST /v1/investor-relations/generate - Generate investor package")
    print(f"  POST /v1/investor-relations/market-context - Fetch FRED/Alpha context")
    print(f"  POST /v1/critical-minerals/context - Generate critical minerals and tariff context")
    print(f"  POST /v1/veris/simulate - Run Veris scenario simulation")
    print(f"  POST /v1/veris/briefing - Build Veris-ready context briefing")
    print(f"  POST /v1/veris/export - Build Veris memory export packet")
    print(f"  GET  /health               - Health check")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cubiczan-MoE-7B Inference Server")
    parser.add_argument("--test", action="store_true", help="Run test query")
    parser.add_argument("--interactive", action="store_true", help="Interactive chat mode")
    parser.add_argument("--port", type=int, default=8000, help="API server port")
    args = parser.parse_args()

    if args.test:
        run_test()
    elif args.interactive:
        run_interactive()
    else:
        run_server(args.port)
