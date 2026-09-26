# AI-native Value Transfer Engine

## CrossBorder Settlement Intelligence

An AI-first Value Transfer Engine (VTE) for investigating how value could move between countries, gathering evidence about candidate routes, evaluating applicability, and selecting or recommending an eligible route.

The project explores whether AI can discover cross-border value-transfer mechanisms without assuming that a predefined provider, payment rail, or banking network is automatically the correct answer.

---

## Vision

> **Tell us where you need value to go → VTE figures out how → value arrives in a form the recipient can use.**

A value-transfer request may involve banks, payment providers, correspondent networks, fintechs, digital assets, local payment systems, cards, cash pickup, or other mechanisms.

VTE treats these as possible mechanisms to investigate rather than assuming one of them in advance.

---

## What is VTE?

The Value Transfer Engine is an AI-first architecture for cross-border value-transfer investigation and orchestration.

The current project focuses on:

```text
Discover
   ↓
Investigate
   ↓
Validate
   ↓
Determine Eligibility
   ↓
Select / Recommend
```

The longer-term architecture extends this flow to execution and delivery confirmation:

```text
Discover
   ↓
Investigate
   ↓
Validate
   ↓
Determine Eligibility
   ↓
Select
   ↓
Execute / Coordinate
   ↓
Confirm Delivery
```

The current work concentrates on AI-driven route discovery, evidence collection, route investigation, regulatory/compliance evaluation, eligibility, and recommendation.

Execution, coordination, settlement monitoring, and delivery confirmation are future stages of the architecture.

---

# Architecture

The governing VTE architecture is:

```text
USER / BUSINESS
       │
       ▼
AI PAYMENT AGENT
       │
       ▼
PAYMENT INTENT
       │
       ▼
INTELLIGENCE
       │
       ├── Financial Intelligence
       ├── Route Intelligence
       ├── Settlement Intelligence
       ├── Regulatory Evidence
       ├── Fraud / Risk Intelligence
       └── External Intelligence
       │
       ▼
NORMALIZED INTELLIGENCE
       │
       ▼
AI ROUTE DISCOVERY
       │
       ▼
ROUTE INVESTIGATION
       │
       ▼
AI-LED COMPLIANCE / ELIGIBILITY
       │
       ▼
ROUTE SELECTION / RECOMMENDATION
       │
       ▼
EXECUTION / COORDINATION
       │
       ▼
DELIVERY CONFIRMATION
```

The architecture deliberately separates **what the system knows** from **how the system uses that information to make a route decision**.

---

## Current vs Longer-Term Architecture

The current project focuses on:

```text
Discover
   ↓
Investigate
   ↓
Validate
   ↓
Determine Eligibility
   ↓
Select / Recommend
```

The longer-term architecture extends this flow to execution and delivery confirmation:

```text
Discover
   ↓
Investigate
   ↓
Validate
   ↓
Determine Eligibility
   ↓
Select
   ↓
Execute / Coordinate
   ↓
Confirm Delivery
```

---

# Intelligence vs Decision Architecture

## Intelligence

The Intelligence Layer answers:

> **What do we know?**

It gathers and normalizes information relevant to a value-transfer request, including:

- financial conditions
- currencies and FX
- payment mechanisms
- route and provider information
- settlement mechanisms
- blockchain and on-chain activity
- regulatory evidence
- fraud and counterparty risk
- external intelligence

## Decision Architecture

The decision architecture answers:

> **How should we use what we know?**

AI discovers candidate routes.

Candidate routes are then investigated against available evidence.

Regulatory and compliance assessment uses applicable evidence and AI reasoning.

The system determines whether a candidate is eligible for the specific value-transfer intent and can then select or recommend an appropriate route.

This separation is intentional:

```text
What do we know?
       ↓
INTELLIGENCE
       ↓
What does the evidence tell us?
       ↓
INVESTIGATION
       ↓
Is this route applicable and eligible?
       ↓
ELIGIBILITY
       ↓
Which eligible route should be selected or recommended?
       ↓
ROUTE DECISION
```

---

# AI-first Route Discovery

A central design principle is:

> **Do not assume the route before investigating it.**

The system does not hard-code a particular provider or payment rail as the answer.

AI can discover candidate mechanisms including:

- bank transfers
- correspondent banking
- fintech and remittance services
- mobile money
- local payment systems
- card networks
- digital assets
- P2P mechanisms
- cash-based mechanisms
- trade-related settlement mechanisms

These are candidate hypotheses.

They are not automatically treated as verified financial infrastructure.

A route discovered by a model must be investigated and validated before it can be treated as an operationally usable route.

---

# Evidence-Driven Design

A central lesson from the experiments is:

> **Plausible AI-generated routes are not necessarily real routes.**

A model can generate a convincing provider, banking path, payment rail, transfer mechanism, or route requirement that may not actually be available for a particular corridor.

VTE therefore preserves the distinction between:

```text
AI-generated candidate
        ↓
Evidence investigation
        ↓
Validation
        ↓
Eligibility determination
        ↓
Usable route
```

Raw model responses are preserved as experimental evidence.

Unsupported, stale, conflicting, or incorrect model assumptions are not silently converted into facts.

---

# Route Discovery Evaluation

The project includes an evaluation harness for comparing AI route-discovery behavior across models.

The main route-discovery matrix uses:

- 21 countries
- directed cross-border corridors
- structured route objects
- local and hosted AI models
- repeatable evaluation harnesses
- preserved model outputs

The structured route contract includes fields such as:

```text
route_id
source
destination
rail
funding_method
transfer_path
delivery_method
route_requirements
corridor_availability
```

The evaluation preserves:

- raw AI responses
- model/provider information
- execution status
- timing information
- candidate routes
- experiment constraints
- semantic validation results

This makes model behavior observable rather than reducing an experiment to a single final answer.

---

# Cross-Model Evaluation

The route-discovery experiments include multiple models and providers.

Examples include:

- NVIDIA Nemotron
- Qwen
- Gemma
- Mistral
- Llama
- Phi
- DeepSeek
- other hosted models

The experiments show variation between models in:

- candidate-route generation
- structured-output behavior
- execution reliability
- route diversity
- payment-mechanism assumptions
- response latency

The purpose of the evaluation is to characterize model behavior.

A model's generated route is experimental evidence, not independent proof that the route exists.

---

# NVIDIA Nemotron

For the Nebius × NVIDIA Global AI Hackathon, the project evaluated:

```text
nvidia/nemotron-3-super-120b-a12b
```

The model was used for route-discovery experimentation across the 21-country matrix.

One canonical Nemotron route-discovery result contains:

```text
Directed corridors:       420
Corridor records:         420
Candidate route objects:  1,722
```

The resulting route objects use the VTE route contract.

Nemotron output is treated as candidate evidence rather than verified financial truth.

---

# Why Nemotron?

Cross-border route discovery requires reasoning across multiple dimensions, including:

- source and destination countries
- source and destination currencies
- funding mechanisms
- transfer paths
- payment rails
- settlement mechanisms
- recipient delivery methods
- route requirements
- regulatory context
- changing external conditions

Nemotron was therefore evaluated as one of the larger hosted models in the VTE model-comparison experiments.

The project does not assume that one model is universally correct.

---

# Nebius

Nebius was used as a hosted model-inference environment for the large-model evaluation.

The VTE route-discovery harness is provider-neutral:

```text
VTE Route Discovery Harness
          │
          ├── Local Models
          │
          ├── Nebius / NVIDIA Models
          │
          └── Other Hosted Models
```

This allows the same evaluation methodology to be applied across different model environments.

The Nebius/NVIDIA experiment became part of the project's broader model-evaluation and evidence workflow rather than being treated as a separate architecture.

---

# Prompt Engineering

The route-discovery experiments use prompt engineering rather than model fine-tuning.

Prompts define the value-transfer context and route-discovery task while the evaluation harness validates the resulting route structures.

The prompts distinguish between:

- discovering a candidate
- describing a candidate
- asserting evidence
- validating operational availability

The model is not treated as the authoritative source of financial infrastructure availability.

Where a candidate requires external verification, it remains a hypothesis for downstream investigation.

---

# SWIFT Experiments

The project includes controlled experiments around SWIFT availability.

The purpose of these experiments is to investigate whether an AI model can discover alternative operational mechanisms when SWIFT is excluded from the experiment.

The validation is semantic rather than simple keyword matching.

A candidate can violate the experimental constraint if SWIFT appears as an operational dependency in:

- the rail
- transfer path
- route requirements
- another operational field

A negative statement such as "excluding SWIFT" does not make an operational SWIFT dependency valid.

Violating candidates are preserved as evidence rather than silently deleted or repaired.

---

# AliceAI Experiment

The project also includes a separate raw route-discovery experiment using:

```text
yandex/AliceAI-Foundation-80B-A3B-Base
```

This experiment was intentionally kept separate from the structured VTE route contract.

AliceAI Foundation is a base model, and the experiment therefore focused on raw candidate discovery rather than forcing the output into the structured route schema.

The experiment covered:

```text
Directed corridors:       100
Successful calls:         100
Errors:                   0
Average runtime:          7.26 seconds
Completion limit:         1,500 tokens
```

The raw experiment produced:

```text
Explicit candidate headings: 196
Unique candidate labels:     122
```

The outputs included candidate mechanisms such as:

- correspondent banking
- fintech/remittance
- cryptocurrency
- P2P exchange
- mobile money
- local payment systems
- cash pickup
- trade-related mechanisms
- hawala
- card mechanisms

These outputs remain experimental evidence and are not treated as verified route availability.

---

# Regulatory and Compliance Architecture

Compliance is designed as an AI-led investigation using applicable regulatory and compliance evidence.

The current VTE architecture does not treat a fixed deterministic compliance-rule set as the active decision authority.

The intended flow is:

```text
Candidate Route
      ↓
Applicable Regulatory Evidence
      ↓
AI Regulatory / Compliance Investigation
      ↓
Eligibility Determination
```

Earlier deterministic compliance code may remain in the repository as historical or reference material, but it does not define the new AI-led route decision architecture.

---

# Route Eligibility

Eligibility is evaluated in the context of the specific value-transfer intent.

A route is not considered usable merely because:

- a model generated it
- a provider name appears plausible
- the payment rail exists somewhere
- the route worked in another country pair
- a historical route existed
- a route is technically possible in isolation

Eligibility depends on the relevant evidence and requirements for the particular transfer.

---

# User Context

The value-transfer requirement can contain more than:

```text
source country
destination country
amount
currency
```

Future intent enrichment can include requirements such as:

```text
residency
stay type
destination access
recipient requirements
desired receipt form
delivery deadline
```

For example, the difference between:

```text
Business → Business
```

and:

```text
Temporary Visitor → Recipient
```

may materially change which routes are actually usable.

This is part of the reason VTE separates route discovery from route investigation and eligibility.

---

# Technology

Primary technologies include:

- Python
- AI / LLM inference
- REST APIs
- OpenAI-compatible model APIs
- JSON
- Docker
- PostgreSQL-oriented application architecture
- blockchain and on-chain data sources
- financial intelligence sources
- regulatory evidence
- external tool integrations
- Git and GitHub

The architecture is intentionally model- and provider-neutral.

---

# Repository Structure

```text
value-transfer-engine/
│
├── ai/
│   ├── model_interface.py
│   ├── nebius_ai.py
│   ├── ollama_ai.py
│   ├── real_ai.py
│   └── tokenharbor_ai.py
│
├── compliance/
├── eligibility/
├── intelligence/
├── intent/
├── models/
├── pipeline/
├── recommendation/
├── route_discovery/
├── route_selection/
│
├── tests/
│
├── test_results/              # Local/generated; ignored by Git
├── evidence_archive/          # Local/generated; ignored by Git
│
├── LICENSE
├── README.md
└── .gitignore
```

Generated experimental evidence is intentionally separated from the core source repository.

---

# Running the Evaluation Harness

Clone the repository:

```bash
git clone https://github.com/ashishwarkhade/AI_native_Value_Transfer_Engine.git
cd AI_native_Value_Transfer_Engine
```

The route-discovery model-matrix harness is located at:

```text
tests/test_brics_route_discovery_model_matrix.py
```

The harness requires a provider and model.

For example, with Ollama:

```bash
PYTHONPATH=. python tests/test_brics_route_discovery_model_matrix.py \
  --provider ollama \
  --model gemma3:4b
```

The current command-line options are:

```text
--provider {ollama,nebius,tokenharbor}
--model MODEL
--limit LIMIT
--pause PAUSE
--timeout TIMEOUT
--fresh
--exclude-swift
```

Run:

```bash
PYTHONPATH=. python tests/test_brics_route_discovery_model_matrix.py --help
```

to see the current command-line interface.

Provider credentials and local configuration are intentionally not committed to the repository.

---

# Evidence and Reproducibility

The evaluation harness preserves experimental evidence including:

- model/provider
- corridor
- raw model response
- structured route output
- execution status
- timing
- experiment constraints
- semantic validation results

Generated results are stored locally under `test_results/` and related evidence directories.

These generated artifacts are excluded from Git by `.gitignore`.

The repository therefore contains the reproducible evaluation code while large generated datasets remain separate from the source tree.

---

# Important Limitations

This project is an experimental AI-assisted value-transfer architecture.

It is not:

- a bank
- a payment processor
- a money transmitter
- a regulated settlement service
- a guarantee that a discovered route is operational
- legal or regulatory advice

Model-generated routes are hypotheses requiring independent verification.

A route appearing in experimental output does not establish:

- provider availability
- regulatory approval
- legal permissibility
- sanctions clearance
- settlement finality
- actual pricing
- actual delivery time
- current operational availability

External evidence and downstream validation are required before a route can be treated as usable.

---

# Current Project Status

The current focus is:

```text
AI Route Discovery
        ↓
Evidence Collection
        ↓
Route Investigation
        ↓
AI-led Regulatory / Compliance Evaluation
        ↓
Eligibility
        ↓
Route Recommendation
```

Future stages include:

```text
Route Selection
        ↓
Execution / Coordination
        ↓
Settlement Monitoring
        ↓
Delivery Confirmation
```

The project deliberately separates the experimental route-discovery capability from future payment execution.

---

# Hackathon

This project is being developed for the:

**Nebius × NVIDIA Global AI Hackathon**

Project:

**CrossBorder Settlement Intelligence**

Track:

**Best Apps and Agents**

Hackathon-related model evaluation includes:

```text
NVIDIA Nemotron-3-Super-120B-A12B
```

on Nebius-hosted inference.

The project existed before the hackathon submission period and was significantly expanded during the submission period into the current AI-first VTE architecture and model-evaluation workflow.

---

# License

Copyright 2026 Ashish Warkhade

Licensed under the Apache License, Version 2.0.

See [LICENSE](LICENSE) for the full license text.

---

# Repository

GitHub:

https://github.com/ashishwarkhade/AI_native_Value_Transfer_Engine