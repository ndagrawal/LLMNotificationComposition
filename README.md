# LLMNotificationComposition

**LLM-Based Intelligent Notification Composition: From Static Personalization to Context-Aware Persuasive Messaging**

> A systematic survey and architectural framework for using Large Language Models to transform push notifications from static, slot-filled templates into context-aware, persuasive, and adaptive messages. Reference implementation and documentation for the research paper by Nilesh Agrawal (2026).

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![ACM Format](https://img.shields.io/badge/Format-ACM%20sigconf-red.svg)
![Status: Published](https://img.shields.io/badge/Status-Published-green.svg)
![Author](https://img.shields.io/badge/Author-Nilesh%20Agrawal-orange.svg)

---

## 📖 Research Paper & Documentation

All documentation, including the full ACM-formatted paper, LaTeX source, Word document, and presentation slides, is available in the [`docs/`](./docs/) directory:

- 📄 **[ACM Paper (PDF)](./docs/LLM_Notification_Composition_ACM_Paper.pdf)** — Full ACM `sigconf`-formatted research paper.
- 📝 **[LaTeX Source](./docs/LLM_Notification_Composition_ACM_Paper.tex)** — ACM `sigconf` LaTeX source files.
- 📃 **[Word Document](./docs/LLM_Notification_Composition_Paper.docx)** — Editable Word version.
- 📊 **[Presentation Slides (PDF)](./docs/LLM_Notification_Composition_Slides.pdf)** — 19-slide deck summarizing the framework.
- 📑 **[Presentation Slides (PPTX)](./docs/LLM_Notification_Composition_Slides.pptx)** — Editable PowerPoint version.
- 📚 **[BibTeX References](./docs/references.bib)** — Full bibliography with all 28 references.

---

## 🎯 The Core Argument

Modern notification systems are highly effective at deciding **who** to notify, **when** to notify, and **what** to recommend — but they remain weak at deciding **how** to communicate.

Consider a user with a historical preference for pizza receiving a dinner-time notification at 6 PM:

| Approach | Message |
|---|---|
| **Conventional (Slot-Filling)** | *"Order your favorite pizza now."* |
| **Intelligent Composition (LLM)** | *"It's the perfect time for dinner — your usual pizza spot is nearby, and their sweet-and-savory pineapple special might be worth trying tonight."* |

The LLM-enabled message incorporates temporal context, prior taste signals, and controlled novelty to produce a more persuasive, context-sensitive, and action-inducing framing. This is the shift from **relevance** to **intelligence**.

---

## ✨ Key Contributions

1. **Systematic Survey** — PRISMA-guided review of 28 primary sources (2018–2026) across arXiv, ACM DL, IEEE Xplore, and industry engineering blogs, with a three-tier evidence classification scheme.

2. **Architectural Disentanglement** — An explicit attribution matrix separating what LLMs contribute (message generation, style adaptation) from what adjacent systems contribute (audience selection, content ranking, send-time optimization).

3. **Unified Framework** — A complete end-to-end notification pipeline integrating:
   - Budget-aware routing (CLV-tiered LLM vs. template allocation)
   - Retrieval-Augmented Generation (RAG) for grounded composition
   - Parameter-Efficient Fine-Tuning (PEFT/LoRA) for domain adaptation
   - Pairwise reward modeling for candidate ranking
   - Contextual bandits for send-time optimization
   - Frequency capping and factuality guardrails
   - Online learning feedback loop

4. **Critical Evaluation Framework** — Analysis of offline-online metric mismatch, causal inference challenges (SUTVA violations), heterogeneous treatment effects, and the ethical boundary between personalization and manipulation.

---

## 🏗 Architecture

The unified pipeline processes each notification through seven stages:

```
[ User Profile ]  [ Content Inventory ]  [ Real-Time Context ]
        |                  |                      |
        +------------------+----------------------+
                           |
                    [ Budget Router ]
                    (CLV-based: LLM vs. Template)
                           |
              ┌────────────┴────────────┐
              │                         │
        [ RAG Retrieval ]        [ Template Path ]
        [ PEFT/LoRA LLM ]
              │
        [ Candidate Pool ]
              │
        [ Factuality Guard ]
        [ Policy Filter ]
              │
        [ Reward Model Ranking ]
        [ Diversity Filter ]
        [ Frequency Cap ]
              │
        [ STO Bandit ]
        (Send-Time Optimization)
              │
        [ Delivery ]
              │
        [ KPI Logger ]
              │
        [ Online Learning ]
        (Counterfactual Update → Reward Model)
        (Preference Update → RAG Retrieval)
```

---

## 📊 Domain Applications

The framework is evaluated across three production domains:

| Domain | Key System | Primary Technology | Reported Lift | Evidence Tier |
|---|---|---|---|---|
| **Social Media** | Kuaishou PushGen | SFT + Pairwise Reward Model | +8.0% CTR | T1 (Peer-reviewed) |
| **Social Media** | Instagram Diversity Ranking | Diversity-Aware Bandit | +14.5% long-term retention | T2 (Engineering blog) |
| **Food Delivery** | DoorDash GNN | Graph Neural Network + LLM | +1.0% CTR | T2 (Engineering blog) |
| **E-Commerce** | LLM Content Optimizer | Prompt Engineering + A/B | +12% conversion | T2 (Engineering blog) |

---

## 🔬 Figures

| Figure | Description |
|---|---|
| ![PRISMA](./docs/figures/fig1_prisma.png) | **Fig 1:** PRISMA literature screening funnel |
| ![Pipeline](./docs/figures/fig2_pipeline.png) | **Fig 2:** Unified LLM notification pipeline |
| ![Domain Matrix](./docs/figures/fig3_domain.png) | **Fig 3:** Domain generalizability matrix |
| ![Evaluation](./docs/figures/fig4_evaluation.png) | **Fig 4:** Multi-tier evaluation framework |

---

## 📋 Citation

```bibtex
@inproceedings{agrawal2026llmnotification,
  author    = {Agrawal, Nilesh},
  title     = {LLM-Based Intelligent Notification Composition: From Static Personalization
               to Context-Aware Persuasive Messaging},
  booktitle = {Proceedings of the ACM Web Conference},
  year      = {2026},
  address   = {Seattle, WA, USA},
  publisher = {ACM},
  note      = {Survey and Architectural Framework}
}
```

---

## 🤝 Contributing

Contributions, corrections, and extensions are welcome. Please open an issue to discuss proposed changes before submitting a pull request.

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](./LICENSE) file for details.

---

**Nilesh Agrawal** · Seattle, WA, USA · [nilesh.d.agrawal@gmail.com](mailto:nilesh.d.agrawal@gmail.com) · [linkedin.com/in/nileshdagrawal](https://www.linkedin.com/in/nileshdagrawal/)
