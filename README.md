# TruthLens

> A research-oriented multimodal AI prototype for analyzing misinformation and potentially manipulated media across visual, textual, and temporal signals.

## Overview

TruthLens is an experimental multimodal AI system I am building to explore a problem that is becoming increasingly difficult to ignore: online content is consumed and shared faster than it can be meaningfully verified.

Misinformation is rarely a single-modality problem. A misleading post may contain:

- an AI-generated or manipulated image,
- a deepfake or altered video,
- an authentic image presented in the wrong context,
- a misleading textual claim,
- conflicting signals across different modalities,
- or several of these at once.

Many detection systems reduce this complexity to a single binary prediction:

```text
REAL / FAKE
```

TruthLens explores a broader direction: combining multiple specialized models, multimodal signals, evaluation workflows, and system-level analysis rather than relying on one isolated classifier.

The current repository contains a web application, Python backend components, model-training infrastructure, evaluation utilities, and a dedicated benchmarking suite.

---

## Project Status

**Early research prototype — under active development**

TruthLens is not a finished production system, and I do not consider the underlying misinformation-detection problem solved.

The current prototype represents the first stage of a larger research direction. A significant amount of work still needs to be done around:

- multimodal fusion,
- uncertainty and calibration,
- conflicting model outputs,
- evidence quality,
- provenance,
- robustness,
- cross-dataset generalization,
- explanation faithfulness,
- and real-world validation.

I am actively researching these areas while continuing to iterate on the prototype.

My longer-term goal is to narrow this work into a rigorous research problem, evaluate it against meaningful baselines, and investigate whether the results can support a genuine research contribution. If the eventual findings demonstrate sufficient novelty, rigor, and reproducibility, I plan to develop part of this work toward a research paper.

---

## Why TruthLens?

The central difficulty is that misinformation can emerge from different combinations of content and context.

For example:

```text
Manipulated image + false caption
Authentic image + false context
Authentic video + misleading claim
Synthetic media + partially true text
Conflicting visual and textual signals
```

This creates several difficult questions:

- What happens when an image appears authentic but the accompanying claim is false?
- What happens when one model detects suspicious signals while another does not?
- How should confidence be interpreted when different modalities disagree?
- How should the system behave when available evidence is incomplete?
- When should a model abstain instead of forcing a prediction?
- How can a final finding remain traceable to the observations that influenced it?

TruthLens is my attempt to investigate these questions through an evolving multimodal system rather than treating verification as a simple classification task.

---

## Current Project Scope

The repository currently includes work across four major areas.

### 1. Web Application

The product-facing application is built using a modern TypeScript-based frontend stack.

Current technologies include:

- Next.js
- React
- TypeScript
- Tailwind CSS
- Framer Motion
- Recharts
- Lucide React

The application layer is intended to provide an interface between user-submitted content and the underlying analysis workflow.

### 2. Python Backend

The repository contains a Python backend with:

- backend application modules,
- supporting scripts,
- dependency management,
- inference testing,
- model-training entry points.

The backend is being developed as the processing and inference layer connecting model experimentation with the application.

### 3. Training and Evaluation Infrastructure

The `training/` package separates concerns across:

- data handling,
- evaluation,
- model implementations,
- model registry logic,
- training configuration.

This structure supports continued experimentation rather than treating the current models as final or universally reliable.

### 4. Benchmarking Infrastructure

TruthLens includes a dedicated benchmarking suite for studying model and pipeline performance.

The current benchmarking structure includes work around:

- model-level benchmarks,
- multimodal pipeline benchmarks,
- latency measurement,
- throughput testing,
- profiling,
- hardware and device probing,
- benchmark result handling,
- CPU and AMD GPU execution environments.

The benchmarking workflow references model families including:

- EfficientNetV2
- BiLSTM
- Vision Transformer
- multimodal fusion pipelines

It also includes infrastructure related to AMD ROCm and ONNX Runtime ROCm experimentation.

---

## Repository Structure

```text
Truth_Lens/
├── app/                    # Next.js application routes and pages
│
├── backend/
│   ├── app/                # Python backend application modules
│   ├── scripts/            # Backend utility scripts
│   ├── requirements.txt    # Backend dependencies
│   ├── test_inference.py   # Inference testing
│   └── train_models.py     # Model training entry point
│
├── benchmarking/
│   ├── api/                # Benchmark-related API components
│   ├── benchmarks/         # Benchmark implementations
│   ├── profiling/          # Profiling utilities
│   ├── results/            # Benchmark result handling
│   ├── benchmark_runner.py # Benchmark orchestration
│   ├── config.py           # Benchmark configuration
│   └── device_probe.py     # Hardware/device inspection
│
├── components/             # Reusable frontend components
├── data/                   # Project data resources
├── lib/                    # Shared application utilities
├── public/                 # Static assets
│
├── training/
│   ├── data/               # Training data pipeline
│   ├── eval/               # Evaluation code
│   ├── models/             # Model implementations
│   ├── registry/           # Model registry
│   ├── config.py           # Training configuration
│   └── requirements_training.txt
│
├── types/                  # TypeScript type definitions
├── AGENTS.md               # Agent-oriented development context
├── CLAUDE.md               # Claude-oriented project context
└── README.md
```

---

## High-Level Architecture

TruthLens is organized around the following broad system direction:

```text
                    ┌─────────────────────┐
                    │     User Input      │
                    │   Media / Content   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Web Application   │
                    │ Next.js + TypeScript│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Python Backend    │
                    │ Processing/Inference│
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
     ┌────────────────┐ ┌──────────────┐ ┌──────────────┐
     │ Visual Models  │ │Sequence/Text │ │ Transformer  │
     │ EfficientNetV2 │ │    Models    │ │ Experiments  │
     └────────┬───────┘ │    BiLSTM    │ └──────┬───────┘
              │         └──────┬───────┘        │
              └────────────────┼────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Multimodal Pipeline │
                    │   Experimentation   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Evaluation / Output │
                    └─────────────────────┘
```

This diagram represents the high-level project direction. Individual components remain under active development and evaluation.

---

## Model and Pipeline Experimentation

The repository contains infrastructure around multiple model families and experimental workflows.

### EfficientNetV2

Used within visual-model experimentation and benchmarking workflows.

### BiLSTM

Included within sequence-model experimentation and benchmarking workflows.

### Vision Transformer

ViT-based evaluation is represented within the benchmarking infrastructure.

### Multimodal Fusion

The project includes experimentation and benchmarking around multimodal fusion pipelines.

The existence of these components should not be interpreted as a claim that combining them automatically produces a reliable misinformation detector. Determining how different signals should be combined, calibrated, evaluated, and stress-tested remains part of the ongoing research.

---

## Current Research

The current prototype has raised several questions that I am actively investigating.

### 1. Multimodal Fusion

Combining outputs from different model families is not simply a matter of averaging confidence scores.

Current research questions include:

- How should visual and textual signals be weighted?
- What should happen when modalities disagree?
- Should one modality ever override another?
- How should missing modalities be handled?
- How can fusion avoid amplifying weaknesses from individual models?

This remains an active research area within the project.

### 2. Uncertainty and Calibration

A model can be confidently wrong.

One of the areas I am researching is how TruthLens should distinguish between:

- raw model confidence,
- empirical reliability,
- insufficient evidence,
- conflicting evidence,
- and genuine uncertainty.

A long-term objective is to avoid presenting a precise-looking score as if it were proof.

### 3. Evidence Quality

Misinformation analysis is not only a classification problem.

Even when supporting or contradicting information is available, difficult questions remain:

- Is the evidence actually relevant to the claim?
- Is the source reliable?
- Is the information outdated?
- Are multiple sources independent?
- Are several sources merely repeating the same original report?
- Does failure to find evidence mean that a claim is false?

These questions are not fully solved in the current prototype.

### 4. Provenance

I am investigating how future iterations of TruthLens could preserve a clearer relationship between:

```text
Input
  ↓
Model Observation
  ↓
Supporting or Contradicting Evidence
  ↓
Intermediate Reasoning
  ↓
Final Finding
```

The goal is to make important findings more traceable instead of relying only on fluent generated explanations.

**A complete provenance system is not currently claimed as implemented. This is an active research direction.**

### 5. Conflicting Signals

Real-world cases do not always produce agreement.

For example:

- a manipulated image may accompany a true claim,
- an authentic image may accompany a false claim,
- two external sources may disagree,
- different models may produce contradictory outputs.

I am researching how such disagreement should be represented explicitly rather than forcing every case into artificial consensus.

### 6. Generalization

A model that performs well on one dataset may fail on:

- unseen manipulation methods,
- newer generative models,
- social-media compression,
- screenshots,
- low-resolution content,
- different languages,
- different domains,
- or different content distributions.

Cross-dataset and out-of-distribution evaluation are therefore important parts of the planned research.

### 7. Explainability

A convincing explanation is not necessarily a faithful explanation.

One of the core questions I am exploring is how to distinguish between:

- what a model directly observed,
- what available evidence supports,
- what the system inferred,
- and what remains unknown.

---

## Research Questions

TruthLens is currently evolving around questions such as:

1. How should heterogeneous model outputs be fused without creating false confidence?
2. How should uncertainty propagate across a multimodal pipeline?
3. How can conflicting signals be represented explicitly?
4. How should evidence quality be evaluated?
5. How can findings remain traceable to supporting observations?
6. How robust are models under compression and distribution shift?
7. When should the system abstain rather than classify?
8. How should multimodal misinformation systems be evaluated beyond raw accuracy?
9. Can explanations remain grounded in actual model evidence?
10. How can failure cases be systematically documented and learned from?

These questions remain under active investigation.

---

## AMD GPU Benchmarking

TruthLens includes dedicated benchmarking infrastructure for studying model and pipeline performance across CPU and AMD GPU environments.

The suite contains infrastructure for:

- model-level benchmarking,
- multimodal pipeline benchmarking,
- latency measurement,
- throughput testing,
- profiling,
- hardware probing,
- benchmark-result handling.

The benchmarking environment includes work related to:

- AMD ROCm,
- PyTorch GPU execution pathways,
- ONNX Runtime ROCm,
- warm-up iterations,
- repeated latency measurement,
- throughput evaluation.

Install benchmarking dependencies with:

```bash
pip install -r benchmarking/requirements_benchmark.txt
```

Run the benchmark orchestrator with:

```bash
python -m benchmarking.benchmark_runner
```

Hardware-specific results should be independently reproduced before being treated as validated performance claims.

---

## Current Limitations

TruthLens is an early prototype and currently has significant limitations.

### Not a Truth Oracle

The system cannot determine objective truth in every case.

### Model Confidence Is Not Proof

A high model confidence score does not guarantee correctness.

### Dataset Bias

Performance may depend heavily on the datasets used during training and evaluation.

### Domain Shift

Models may fail on unseen manipulation techniques or content distributions.

### Conflicting Modalities

The correct treatment of disagreement between model outputs remains an open research problem.

### Evidence Reliability

External information can itself be inaccurate, duplicated, outdated, or misleading.

### Explainability

Generated explanations can sound plausible without faithfully representing the actual reason behind a model output.

### Calibration

Raw confidence outputs should not automatically be interpreted as calibrated probabilities.

### Adversarial Robustness

The system has not yet been established as robust against deliberate adversarial attacks.

### Real-World Validation

Substantial evaluation is still required before any high-stakes real-world use.

---

## Evaluation Direction

Accuracy alone is not sufficient for a system like TruthLens.

The research roadmap includes evaluation across dimensions such as:

| Dimension | Research Question |
|---|---|
| Classification | How accurately does a component perform on its target task? |
| Precision / Recall | What types of errors dominate? |
| Calibration | Does confidence correspond to observed correctness? |
| Robustness | Does performance survive realistic transformations? |
| Generalization | Does the model work outside its training distribution? |
| Latency | Can inference run within practical constraints? |
| Throughput | How does the system behave under repeated workloads? |
| Cross-device performance | How do CPU and GPU environments compare? |
| Fusion quality | Does combining modalities actually improve results? |
| Abstention | Can the system avoid unsupported decisions? |

Not all of these evaluation objectives are complete today.

---

## Research Roadmap

### Phase 1 — Prototype Stabilization

- [ ] Stabilize the end-to-end application flow
- [ ] Improve backend and frontend integration
- [ ] Strengthen input validation
- [ ] Improve failure handling
- [ ] Document reproducible setup
- [ ] Add representative test cases

### Phase 2 — Model Evaluation

- [ ] Evaluate individual model families separately
- [ ] Establish stronger baselines
- [ ] Document dataset splits
- [ ] Measure precision, recall, F1, and calibration
- [ ] Add structured failure analysis
- [ ] Test cross-dataset generalization

### Phase 3 — Multimodal Fusion Research

- [ ] Compare fusion strategies
- [ ] Study modality disagreement
- [ ] Evaluate missing-modality behavior
- [ ] Investigate confidence propagation
- [ ] Run ablation studies

### Phase 4 — Evidence and Provenance

- [ ] Design source-linked evidence representation
- [ ] Separate observations from hypotheses
- [ ] Preserve evidence metadata
- [ ] Represent conflicting evidence explicitly
- [ ] Investigate provenance-aware reporting

### Phase 5 — Robustness

- [ ] Test compression sensitivity
- [ ] Test resolution degradation
- [ ] Evaluate unseen manipulation methods
- [ ] Study distribution shift
- [ ] Investigate adversarial failure modes

### Phase 6 — Research Publication Direction

- [ ] Formalize a narrow research hypothesis
- [ ] Select defensible baselines
- [ ] Run controlled experiments
- [ ] Conduct ablation studies
- [ ] Report negative results
- [ ] Evaluate statistical significance where appropriate
- [ ] Prepare a paper only if the findings demonstrate sufficient rigor and novelty

---

## Screenshots

> Screenshots from the current prototype will be added as the interface and end-to-end workflow are stabilized.

<!--
Add real screenshots only.

Example:

### Analysis Interface

![TruthLens Analysis Interface](docs/screenshots/analysis-interface.png)

### Detection Results

![TruthLens Detection Results](docs/screenshots/detection-results.png)

### Benchmark Dashboard

![TruthLens Benchmark Dashboard](docs/screenshots/benchmark-dashboard.png)
-->

---

## Installation

### Prerequisites

- Node.js
- npm
- Python
- pip
- Git

For AMD GPU benchmarking, a compatible ROCm environment is required.

### Clone the Repository

```bash
git clone https://github.com/AnushkaKataria26/Truth_Lens.git
cd Truth_Lens
```

### Frontend Setup

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The application should then be available at:

```text
http://localhost:3000
```

### Backend Setup

Navigate to the backend:

```bash
cd backend
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Backend execution depends on the current application entry point under `backend/app/`.

### Training Dependencies

From the project root:

```bash
pip install -r training/requirements_training.txt
```

### Benchmarking Dependencies

```bash
pip install -r benchmarking/requirements_benchmark.txt
```

Run the benchmark orchestrator:

```bash
python -m benchmarking.benchmark_runner
```

---

## Technology Stack

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- Framer Motion
- Recharts
- Lucide React

### Backend and ML

- Python
- PyTorch-based model workflows
- backend service infrastructure
- model training utilities
- inference utilities

### Model Experimentation

- EfficientNetV2
- BiLSTM
- Vision Transformer
- multimodal fusion workflows

### Performance and Hardware

- AMD ROCm experimentation
- PyTorch GPU execution pathways
- ONNX Runtime ROCm experimentation
- CPU/GPU benchmarking
- latency and throughput profiling

---

## Responsible Use

TruthLens is a research prototype.

It should not currently be used as:

- an authoritative fact-checking system,
- definitive proof that media is manipulated,
- proof that a person created deceptive content,
- a replacement for professional investigators or fact-checkers,
- a basis for legal action,
- a basis for disciplinary action,
- or a high-stakes automated decision system.

Model outputs can be wrong.

Human review remains necessary.

---

## Research Intent

I started TruthLens as a technical project around misinformation and manipulated-media detection. As I worked on the prototype, the problem became much more complex than simply training a classifier.

The project has pushed me toward deeper questions around:

- multimodal disagreement,
- evidence quality,
- uncertainty,
- provenance,
- calibration,
- generalization,
- robustness,
- and explanation faithfulness.

I am actively researching these areas while continuing to develop the prototype.

A considerable amount of work remains, and I do not consider the current system complete. My goal is to keep narrowing the research problem, strengthen the evaluation methodology, compare against meaningful baselines, and determine whether the work can support a genuine research contribution.

If future experiments demonstrate sufficient rigor, novelty, and reproducibility, I plan to develop part of this work toward a research paper.

---

## Author

**Anushka Kataria**

Computer Science undergraduate working across AI/ML, multimodal systems, backend development, and full-stack engineering.

GitHub: `@AnushkaKataria26`

---

## Disclaimer

TruthLens is under active development and research.

The repository contains experimental software and should not be interpreted as a validated production misinformation-detection system.
