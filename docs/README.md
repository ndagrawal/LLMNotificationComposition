# Documentation

This folder contains all research and presentation materials associated with the **LLM-Based Intelligent Notification Composition** paper.

## Contents

| File | Format | Description |
|---|---|---|
| `LLM_Notification_Composition_ACM_Paper.pdf` | PDF | Full ACM `sigconf`-formatted research paper |
| `LLM_Notification_Composition_ACM_Paper.tex` | LaTeX | ACM `sigconf` LaTeX source (compile with `pdflatex` + `bibtex`) |
| `LLM_Notification_Composition_Paper.docx` | Word | Microsoft Word version for editing and annotation |
| `LLM_Notification_Composition_Slides.pdf` | PDF | Research paper presentation slide deck (19 slides) |
| `LLM_Notification_Composition_Slides.pptx` | PowerPoint | Editable PPTX version of the research paper slide deck |
| `LLM_Notification_Composition_SDK_Slides.pdf` | PDF | SDK & Reference Implementation presentation (6 slides) |
| `LLM_Notification_Composition_SDK_Slides.pptx` | PowerPoint | Editable PPTX version of the SDK implementation slide deck |
| `references.bib` | BibTeX | Full bibliography with all 28 references |
| `figures/` | PNG | High-resolution figures: PRISMA flow, pipeline architecture, domain matrix, evaluation framework |

## Paper Abstract

Modern notification systems are highly effective at deciding *who* to notify, *when* to notify, and *what* to recommend — but they remain weak at deciding *how* to communicate. Most production systems still rely on rigid, slot-filled templates that produce relevance without intelligence. This paper presents a systematic survey and architectural framework for LLM-based intelligent notification composition, arguing that the next evolution of notifications is not simply better personalization, but intelligent composition: using LLMs to transform static alerts into context-aware, persuasive, and adaptive messages.

The paper examines how LLMs are being integrated into production notification pipelines across social media, food delivery, and e-commerce, focusing on the technical mechanisms that enable scalable and context-aware generation, including Retrieval-Augmented Generation (RAG), Parameter-Efficient Fine-Tuning (PEFT), pairwise reward modeling, and contextual bandits for send-time optimization. A central contribution is the explicit disentanglement of message generation from adjacent recommender system components, and a unified end-to-end architectural framework with budget-aware routing, grounded generation, candidate ranking, diversity controls, frequency capping, and online learning.

## Figures

| Figure | Description |
|---|---|
| `figures/fig1_prisma.png` | PRISMA literature screening funnel (142 identified → 28 retained) |
| `figures/fig2_pipeline.png` | Unified LLM notification pipeline with feedback loops |
| `figures/fig3_domain.png` | Domain generalizability matrix: Social Media / Food Delivery / E-Commerce |
| `figures/fig4_evaluation.png` | Multi-tier evaluation framework: primary metrics, guardrails, long-horizon |

## Compiling the LaTeX Source

```bash
pdflatex LLM_Notification_Composition_ACM_Paper.tex
bibtex LLM_Notification_Composition_ACM_Paper
pdflatex LLM_Notification_Composition_ACM_Paper.tex
pdflatex LLM_Notification_Composition_ACM_Paper.tex
```

Requires `texlive-full` or equivalent with the `acmart` document class.

## Author

**Nilesh Agrawal**
Seattle, WA, USA
[nilesh.d.agrawal@gmail.com](mailto:nilesh.d.agrawal@gmail.com)
[linkedin.com/in/nileshdagrawal](https://www.linkedin.com/in/nileshdagrawal/)
