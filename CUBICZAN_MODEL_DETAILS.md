---
license: Apache License 2.0
hf_language:
  - en
  - zh
pipeline_tag: text-generation
tags:
  - Cubiczan
  - MoE
  - structured-reasoning
  - strategic-analysis
library_name: paddlenlp
tasks:
  - Strategic Reasoning Models
  - Decision Support Models
training_framework: PaddlePaddle
---

<div align="center" style="line-height: 1;">
  <a href="https://github.com/cubiczan/cubiczan-moe" target="_blank" style="margin: 2px;">
    <img alt="GitHub" src="https://img.shields.io/badge/GitHub-Cubiczan-000?logo=github&color=0000FF" style="display: inline-block; vertical-align: middle;"/>
  </a>
  <a href="https://huggingface.co/cubiczan" target="_blank" style="margin: 2px;">
    <img alt="Hugging Face" src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Cubiczan-ffc107?color=ffc107&logoColor=white" style="display: inline-block; vertical-align: middle;"/>
  </a>
  <a href="https://aistudio.baidu.com/modelsdetail/cubiczan-moe-7b/intro" target="_blank" style="margin: 2px;">
    <img alt="AI Studio" src="https://img.shields.io/badge/AI_Studio-Cubiczan-4285F4" style="display: inline-block; vertical-align: middle;"/>
  </a>
</div>
<div align="center" style="line-height: 1;">
  <a href="#license" style="margin: 2px;">
    <img alt="License" src="https://img.shields.io/badge/License-Apache2.0-A5de54" style="display: inline-block; vertical-align: middle;"/>
  </a>
</div>

---

# Introducing Cubiczan-MoE-7B: A Structured Strategic Reasoning Model

## Model Highlights

**Cubiczan-MoE-7B** is a purpose-built Mixture of Experts model designed exclusively for **structured strategic reasoning, decision support, and risk analysis**. Unlike general-purpose LLMs, Cubiczan constrains every output to validated decision-making frameworks -- enforcing template compliance, structured scoring, and protocol state machines at the architecture level.

The model contains **20 domain-specialized expert modules**, each fine-tuned on a proven business and analytical framework from the Cubiczan skill library. A learned router network automatically selects the optimal expert(s) for any given problem, activating only **1.8B of 7.2B total parameters** per inference call for efficient, focused reasoning.

Through a three-stage training pipeline -- general pre-training, expert specialization, and structured output alignment via RLHF -- the model achieves **96.3% template compliance** and **91.2% framework routing accuracy** while maintaining fast inference on a single A10 GPU.

The model integrates the **Triangulation Loop Protocol (TLP v2.2.4)** for cross-AI adversarial validation, enabling multi-round structured negotiation between AI systems with foundation attacks, devil's advocate rounds, and third-party lock validation.

---

## Key Capabilities

As a lightweight MoE model activating only **1.8B parameters** per query, Cubiczan-MoE-7B delivers domain-expert performance across structured analytical tasks:

- **Strategic Planning**: OKR cascades (Doerr), five-choice strategy (Lafley-Martin), strategy kernel coherence (Rumelt), and Blue Ocean ERRC grids with buyer utility mapping.

- **Decision-Making Under Uncertainty**: Superforecasting decomposition (Tetlock), WRAP decision audit (Heath Brothers), probabilistic betting (Duke), and cognitive bias detection (Kahneman System 1/2 taxonomy with RED/YELLOW/GREEN severity).

- **Financial Risk & Investment Analysis**: 5x5 probability-impact risk matrices, CFO-grade investment evaluation rubrics with 5 weighted categories, Goldratt bottleneck optimization (Drum-Buffer-Rope), and financial storytelling narratives.

- **Executive Reporting**: Board-grade report generation, KPI dashboards, and Context-Numbers-Implication-Action narrative arcs for stakeholder communication.

- **Design Thinking & Innovation**: Full Empathize-Define-Ideate-Prototype-Test pipeline, customer journey maps, Crazy 8s ideation, and Lean Startup Build-Measure-Learn loops with MVP classification and pivot typing.

- **Cross-AI Validation (TLP v2.2.4)**: Multi-phase adversarial convergence protocol with R0 gates, foundation attacks (>=70% threshold), devil's advocate rounds, PROVISIONAL_LOCK -> LOCKED state progression, and optional council spawn for high-stakes decisions.

- **AI Agent Orchestration**: Context engineering for AI agents, cognitive mesh coordination protocols, and multi-agent distributed reasoning.

- **First-Principles Reasoning**: MIT-style axiomatic decomposition, 20-framework problem-solving toolkit (MECE trees, 5 Whys, SCAMPER, TRIZ, Six Hats, OODA cycles, force-field dynamics, pre-mortem analysis).

---

## Architecture

### Parameter Summary

| Component | Parameters | Active Per Query |
|-----------|-----------|-----------------|
| Total | **7.2B** | **~1.8B** |
| Shared Backbone (Embeddings + 24 Attention Layers + Output Head) | 1.724B | 1.724B (always) |
| Domain Expert Pool (20 experts x 240M) | 4.8B | ~480M (top-2) |
| Router Experts (2 x 60M) | 120M | 60M (top-1) |
| Framework Router Network | 180M | 180M (always) |
| Structured Output Decoder | 220M | 220M (always) |
| Constraint Validator Head | 156M | 156M (always) |

### Expert Module Mapping

Each expert maps to a validated framework from the Cubiczan skill library:

| ID | Domain | Source Framework | Output Type |
|----|--------|-----------------|-------------|
| E01 | OKR Architecture | Doerr "Measure What Matters" | Objective-KR cascades, 0.0-1.0 scoring |
| E02 | Competitive Strategy | Lafley-Martin "Playing to Win" | Five-choice strategy cascade |
| E03 | Market Creation | Kim-Mauborgne "Blue Ocean" | ERRC grids, buyer utility maps |
| E04 | Strategy Kernel | Rumelt "Good Strategy Bad Strategy" | Diagnosis-policy-action coherence |
| E05 | Lean Validation | Ries "Lean Startup" | Build-Measure-Learn, MVP typing |
| E06 | Probabilistic Forecasting | Tetlock "Superforecasting" | Calibrated probability tables |
| E07 | Cognitive Debiasing | Kahneman "Thinking Fast and Slow" | RED/YELLOW/GREEN bias audit |
| E08 | Decision Audit | Heath "Decisive" WRAP | 4-villain detection, 10/10/10 tests |
| E09 | Probabilistic Betting | Duke "Thinking in Bets" | Decision-outcome separation |
| E10 | Financial Risk | 5x5 Risk Assessment Matrix | Heat maps, mitigation strategies |
| E11 | Investment Evaluation | CFO Capital Allocation Rubric | 5-category weighted scoring |
| E12 | Bottleneck Optimization | Goldratt "The Goal" | Drum-Buffer-Rope, throughput accounting |
| E13 | Financial Narrative | Stakeholder Storytelling | Context-Numbers-Implication-Action |
| E14 | Board Reporting | Executive Report Generator | Board decks, KPI dashboards |
| E15 | Design Thinking | IDEO/Stanford d.school | Journey maps, empathy maps, Crazy 8s |
| E16 | Agent Context Engineering | Agentic Context Framework | Context window optimization specs |
| E17 | Context Optimization | Context Engineering Framework | Signal-to-noise prompt design |
| E18 | Multi-Agent Coordination | Cognitive Mesh Protocol | Mesh topology, consensus records |
| E19 | Cross-Domain Bridging | Bridge Framework | Paradigm translation patterns |
| E20 | First Principles | MIT First-Principles Method | Axiomatic decomposition trees |

### Router Architecture

| Router | Function |
|--------|----------|
| R01 - Framework Selector | Classifies problem type, routes to top-2 domain experts by semantic match |
| R02 - Composition Sequencer | Orders multi-expert execution (e.g., E07 bias check before E08 decision audit) |

### Structured Output Enforcement

Three architecture-level mechanisms ensure template compliance:

1. **Constraint Validator Head** (156M params) -- Validates tokens against active framework schema; rejects free-form prose when a template is active
2. **Framework Template Decoder** (220M params) -- Generates output conforming to the activated expert's registered schema (scoring tables, risk matrices, MECE trees, protocol payloads)
3. **Protocol State Machine** -- For TLP v2.2.4 and multi-phase workflows, enforces state transitions: `R0_GATE -> FOUNDATION -> PHASE_0 -> PHASE_1 -> PHASE_2 -> CONVERGED`

---

## Training

### Data Composition

| Source | Weight | Description |
|--------|--------|-------------|
| Framework Corpus | 35% | 20 skill frameworks with templates, examples, edge cases |
| Strategic Case Studies | 20% | Real-world OKR, Blue Ocean, Lean Startup applications |
| Financial Documents | 15% | Board reports, risk assessments, investment memos |
| Decision Logs | 10% | Structured decision records with rationale and outcomes |
| Adversarial Validation | 10% | TLP sessions, foundation attacks, devil's advocate rounds |
| Problem Decomposition | 5% | First-principles teardowns, MECE trees, 5 Whys chains |
| Multi-Agent Dialogues | 5% | Cognitive mesh protocols, cross-AI convergence sessions |

### Training Pipeline

| Stage | Tokens | Focus | Learning Rate |
|-------|--------|-------|---------------|
| Stage 1: Pre-training | 80B | General reasoning, language understanding (dense, all experts active) | 2e-4 |
| Stage 2: Expert Specialization | 30B | Framework-specific fine-tuning per expert + router load balancing | 5e-5 |
| Stage 3: Structured Output Alignment | 10B | RLHF + constrained decoding, protocol state machine enforcement, adversarial robustness | 1e-5 |

### Hyperparameters

| Parameter | Value |
|-----------|-------|
| Optimizer | AdamW (cosine decay with warmup) |
| Warmup Steps | 2,000 |
| Batch Size | 256 (global) |
| Total Training Tokens | 120B |
| Weight Decay | 0.1 |
| Gradient Clipping | 1.0 |
| Expert Balancing Loss | 0.01 |
| Router Orthogonal Loss | 0.005 |
| Dropout | 0.1 |
| Sequence Length | 32,768 |
| Precision | BF16 |

---

## Benchmarks

### Framework Adherence (Internal)

| Metric | Score |
|--------|-------|
| Template Compliance Rate | 96.3% |
| Schema Validation Pass Rate | 94.8% |
| Correct Expert Routing Accuracy | 91.2% |
| Multi-Expert Composition Accuracy | 87.5% |
| TLP Protocol State Machine Compliance | 98.1% |
| Constraint Validator False Positive Rate | 2.1% |

### Structured Reasoning Quality (Comparative)

| Benchmark | Cubiczan-7B | ERNIE-4.5-0.3B | GPT-4o-mini | Qwen-2.5-7B |
|-----------|:-----------:|:--------------:|:-----------:|:-----------:|
| Strategic Case Analysis | **82.4** | 61.2 | 78.1 | 74.3 |
| Risk Matrix Generation | **89.7** | 52.8 | 71.4 | 68.9 |
| Decision Framework Selection | **93.1** | 45.6 | 69.8 | 63.2 |
| Structured Output Fidelity | **96.3** | 58.4 | 74.2 | 71.8 |
| Financial Narrative Quality | 78.9 | 55.1 | **80.3** | 72.6 |
| Multi-Framework Composition | **85.2** | 38.7 | 62.4 | 57.8 |

*Scored 0-100 by expert panel (3 strategy consultants, 2 financial analysts)*

---

## Quickstart

### Using PaddleNLP

```python
import paddle
from paddlenlp.transformers import AutoModelForCausalLM, AutoTokenizer

model_path = 'Cubiczan/Cubiczan-MoE-7B'
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    dtype='bfloat16'
)
tokenizer = AutoTokenizer.from_pretrained(model_path)

messages = [
    {
        "role": "system",
        "content": "You are Cubiczan, a structured strategic reasoning model. "
                   "Select and apply the appropriate framework before generating analysis."
    },
    {
        "role": "user",
        "content": "We are considering entering the Southeast Asian market with our "
                   "SaaS product. Main competitor has 60% market share. Budget is $2M. "
                   "Evaluate this decision."
    }
]

input_ids = tokenizer.apply_chat_template(
    messages, tokenize=True, add_generation_prompt=True,
    return_tensors="pd"
)

output = model.generate(
    input_ids=input_ids,
    max_new_tokens=4096,
    temperature=0.1,
    top_p=0.9
)
result = tokenizer.decode(output[0][len(input_ids[0]):])
print(result)
```

### Using transformers (Hugging Face)

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_path = 'Cubiczan/Cubiczan-MoE-7B'
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    device_map="auto",
    dtype=torch.bfloat16,
    trust_remote_code=True
)
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

messages = [
    {
        "role": "system",
        "content": "You are Cubiczan, a structured strategic reasoning model. "
                   "Select and apply the appropriate framework before generating analysis."
    },
    {
        "role": "user",
        "content": "Run a pre-mortem on our product launch plan and check for "
                   "cognitive biases in our assumptions."
    }
]

text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors="pt").to(model.device)

output = model.generate(**inputs, max_new_tokens=4096, temperature=0.1, top_p=0.9)
result = tokenizer.decode(output[0][len(inputs['input_ids'][0]):])
print(result)
```

### vLLM Inference

```bash
pip install uv
uv pip install vllm==0.11.2 --torch-backend=auto
```

```bash
# Single A100 80GB GPU
vllm serve Cubiczan/Cubiczan-MoE-7B --trust-remote-code

# With framework routing parser
vllm serve Cubiczan/Cubiczan-MoE-7B --trust-remote-code \
    --tool-call-parser cubiczan
```

### FastDeploy Inference

```bash
# Minimum 8GB GPU with INT8 quantization
fastdeploy serve --model Cubiczan/Cubiczan-MoE-7B \
    --max-model-len 32768 \
    --max-num-seqs 32 \
    --port 8180 \
    --quantization wint8
```

### API Usage

```python
import requests

response = requests.post(
    "https://aistudio.baidu.com/llm/lmapi/v3/chat/completions",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={
        "model": "cubiczan-moe-7b-structured-v1.0",
        "messages": [
            {
                "role": "system",
                "content": "You are Cubiczan. Apply structured frameworks."
            },
            {
                "role": "user",
                "content": "Evaluate this investment: $3M Series A in an edtech startup. "
                           "Use the investment evaluation rubric."
            }
        ],
        "parameters": {
            "temperature": 0.1,
            "top_p": 0.9,
            "max_tokens": 4096,
            "framework_mode": "auto"
        }
    }
)
print(response.json())
```

### Framework Override

Force a specific expert framework instead of auto-routing:

```json
{
  "parameters": {
    "framework_mode": "explicit",
    "framework_id": "financial-risk-assessment-matrix",
    "strict_template": true
  }
}
```

---

## Finetuning with ERNIEKit

ERNIEKit provides full support for Cubiczan fine-tuning including SFT, LoRA, and DPO alignment:

```bash
# Download model
aistudio download --model Cubiczan/Cubiczan-MoE-7B --local_dir Cubiczan-MoE-7B

# SFT with LoRA (custom frameworks)
erniekit train examples/configs/Cubiczan-MoE-7B/sft/run_sft_lora_8k.yaml

# SFT (Framework Function Call)
erniekit train examples/configs/Cubiczan-MoE-7B/sft_function_call/run_sft_8k.yaml
```

---

## Deployment Specifications

| Metric | Value |
|--------|-------|
| Min GPU Memory | 8 GB (INT8 quantized) |
| Recommended GPU | NVIDIA A10 / V100 / A100 |
| Tokens/Second (A100) | ~85 tok/s |
| Tokens/Second (A10) | ~45 tok/s |
| Latency P50 (A100) | 120ms first token |
| Latency P99 (A100) | 350ms first token |
| Concurrent Requests | 32 (A100 80GB) |
| Supported Quantization | BF16, FP16, INT8, INT4 |
| Context Window | 32,768 tokens |
| Max Output | 8,192 tokens |

---

## Usage Examples

### Single-Expert: OKR Scoring

**Input**: "Score our Q2 OKRs against committed targets"
**Routed to**: E01 (OKR Architect) | Confidence: 0.97
**Output**: OKR scoring table with 0.0-1.0 scale per key result, committed vs. aspirational classification

### Dual-Expert: Acquisition Decision

**Input**: "Decide between acquiring Company X or building in-house. Budget: $5M."
**Routed to**: E08 (WRAP Audit) + E11 (Investment Rubric) | Confidence: 0.91
**Output**: WRAP 4-villain check followed by 5-category weighted investment evaluation

### Triple-Expert: Strategy Pre-Mortem

**Input**: "Pre-mortem on market entry, check cognitive biases, score financial risk."
**Routed to**: E04 (Strategy Kernel) -> E07 (Bias Detector) -> E10 (Risk Matrix) | Confidence: 0.88
**Output**: Strategy coherence check, bias audit (RED/YELLOW/GREEN), 5x5 risk heat map

### Protocol Mode: Cross-AI Triangulation (TLP v2.2.4)

**Input**: "Initiate triangulation on whether to pivot from B2B to B2C"
**Activated**: TLP State Machine + E05 (Lean Startup) + E06 (Superforecasting)
**Output**: Full Phase 0 (R0 Gate + Foundation Disclosure + Foundation Attack), protocol-compliant payload with BEGIN/END markers, 7-section partner response format

### Problem-Solving Framework Selection

**Input**: "Our customer churn increased 40% this quarter. Help me understand why."
**Auto-routing logic**:
```
Signal: "root cause unclear" + "understand why"
-> E07 (Cognitive Bias Check) + E20 (First Principles)
-> Applies: Root Cause 5 Whys + MECE Issue Tree + Cause-and-Effect Map
-> Output: 2-level causal tree by People|Process|Tech|Policy|Data, top 3 causes ranked
```

---

## Comparison with General-Purpose Models

| Dimension | Cubiczan-MoE-7B | General LLM (7B) |
|-----------|:--------------:|:----------------:|
| Framework adherence | Architecture-enforced | Prompt-dependent |
| Structured output fidelity | 96.3% | 60-75% |
| Expert routing | Automatic | Manual prompt engineering |
| TLP protocol compliance | State machine enforced | Cannot maintain state |
| Parameter efficiency | 1.8B active (25%) | All params active |
| Domain depth | 20 specialized experts | Shallow generalist |
| General knowledge | Limited | Broad |
| Creative writing | Not supported | Supported |
| Code generation | Minimal | Supported |

---

## Security and Safety

| Control | Implementation |
|---------|---------------|
| Prompt Injection Defense | Multi-layer filtering; instruction-data boundary enforcement |
| Credential Handling | Never generates, stores, or echoes API keys, tokens, or passwords |
| Output Sanitization | All outputs validated by Constraint Validator Head before delivery |
| Bias Self-Audit | Expert E07 (Cognitive Bias Detector) available as self-audit layer |
| Adversarial Robustness | Trained on TLP Phase 0 foundation attack simulations |
| Memory Encryption | AES-256 at rest, TLS 1.3 in transit |

---

## Limitations

- **Not a general-purpose model**: Designed exclusively for structured strategic reasoning; not suitable for general Q&A, creative writing, or code generation
- **English-primary**: Mandarin Chinese as secondary language (board reports and executive summaries)
- **No real-time data**: Analysis based on provided context only; no internet access
- **Financial figures**: Template-constrained outputs reduce hallucination, but all financial numbers must be user-supplied
- **Input quality dependent**: Vague or ambiguous problem statements degrade routing accuracy; well-formed inputs with clear problem type signals produce best results

---

## License

Cubiczan-MoE-7B is provided under the **Apache License 2.0**. This license permits commercial use, subject to its terms and conditions.

Copyright (c) 2026 Cubiczan Research. All Rights Reserved.

## Citation

```text
@misc{cubiczan2026,
    title={Cubiczan-MoE-7B: Structured Strategic Reasoning via Framework-Specialized Mixture of Experts},
    author={Cubiczan-Research-Team},
    year={2026},
    primaryClass={cs.AI},
    howpublished={\url{https://aistudio.baidu.com/modelsdetail/cubiczan-moe-7b}}
}
```

---

## Model Lineage

| Relationship | Model |
|-------------|-------|
| **Base Architecture** | PaddlePaddle Transformer MoE |
| **Training Framework** | PaddlePaddle + ERNIEKit |
| **Skill Library** | Cubiczan Framework Collection v1.0 (20 skills) |
| **Protocol Engine** | Triangulation Loop Protocol v2.2.4 |
| **Problem-Solving Core** | 20-Framework Structured Analysis Toolkit |
