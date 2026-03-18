# Source Code

This directory contains the Python scripts used to generate the four publication-quality figures in the paper. All figures are generated using `matplotlib` for full control over layout, typography, and colour.

## Requirements

```bash
pip install matplotlib numpy
```

## Scripts

### `draw_pipeline.py`
Generates **Figure 2: Unified LLM Notification Pipeline** — a two-row horizontal flow diagram showing the end-to-end notification composition pipeline with colour-coded swim lanes, budget routing, feedback loops, and operational safeguards.

```bash
python3 draw_pipeline.py
# Output: ../docs/figures/fig2_unified_pipeline.png
```

### `draw_domain.py`
Generates **Figure 3: Domain Generalizability Matrix** — a horizontal 3-column comparison table contrasting Social Media, Food Delivery, and E-Commerce across six dimensions: high-value user definition, primary metric, contextual signals, LLM value, persuasion tolerance, and key challenge.

```bash
python3 draw_domain.py
# Output: ../docs/figures/fig3_domain_generalizability_matrix.png
```

### `draw_evaluation.py`
Generates **Figure 4: Multi-Tier Evaluation Framework** — a 4-tier horizontal layout covering Primary Engagement Metrics, Guardrail Metrics, Long-Horizon Health Metrics, and Threats to Validity.

```bash
python3 draw_evaluation.py
# Output: ../docs/figures/fig4_evaluation_framework.png
```

> **Note:** Figure 1 (PRISMA Literature Screening Funnel) is generated from the Mermaid source at `docs/latex/` and rendered using `manus-render-diagram`.
