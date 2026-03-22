# LLMNotificationComposition

**LLM-Based Intelligent Notification Composition: From Static Personalization to Context-Aware Persuasive Messaging**

> **v3 (March 2026)** — Significantly revised. Three new contributions: six-dimension message quality framework, architectural attribution, and binding-constraint decision framework. See [What's New in v3](#whats-new-in-v3) below.

> A systematic survey and architectural framework for using Large Language Models to transform push notifications from static, slot-filled templates into context-aware, persuasive, and adaptive messages — with a full reference implementation as an iOS SDK and Python backend server.

[![Paper (arXiv)](https://img.shields.io/badge/Paper-arXiv%20Format-red?style=flat-square)](docs/LLM_Notification_Composition_arXiv.pdf)
[![Swift](https://img.shields.io/badge/iOS%20SDK-Swift%205.9+-orange?style=flat-square&logo=swift)](NotifyComposeSDK/)
[![Python](https://img.shields.io/badge/Server-Python%203.11%20FastAPI-blue?style=flat-square&logo=python)](server/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**Author:** Nilesh Agrawal · [nilesh.d.agrawal@gmail.com](mailto:nilesh.d.agrawal@gmail.com) · Seattle, WA  
**LinkedIn:** [linkedin.com/in/nileshdagrawal](https://www.linkedin.com/in/nileshdagrawal/)

---

## What's New in v3

v3 (March 2026) is a significant revision of the paper. The key changes are:

### Three New Contributions (replacing the previous four)

| # | Contribution | Description |
|---|---|---|
| 1 | **Message Quality Framework** | Six-dimension definition of notification message quality with empirical grounding. Replaces CTR as the implicit quality proxy. |
| 2 | **Architectural Attribution** | Explicit disentanglement of the message generation layer from targeting, ranking, and timing. Specifies which gains can be attributed to language quality. |
| 3 | **Binding-Constraint Framework** | Three-criterion decision framework specifying when LLM generation is — and is not — the binding constraint. Includes a principled argument for *when not to use LLMs at all*. |

### New Code: `server/services/message_quality.py`

The primary new code file in v3. Implements:
- **`MessageQualityEvaluator`** — Six-dimension quality scorer (contextual relevance, clarity, actionability, novelty handling, linguistic freshness, persuasive appropriateness).
- **`check_binding_constraint()`** — Three-criterion binding-constraint check. Returns `use_llm=True` only when all three criteria are met.

### Updated: `server/services/pipeline_services.py`

- `route_budget()` now calls `check_binding_constraint()` before routing to the LLM path.
- `_heuristic_reward_rank()` now uses `MessageQualityEvaluator` (six-dimension composite score) instead of the previous ad-hoc heuristic.

### The Six-Dimension Message Quality Framework (Table 1 in v3)

| Dimension | Template | LLM |
|---|---|---|
| Contextual Relevance | Weak — only static slot values | Strong — composes multiple signals naturally |
| Clarity | Variable — slot grammar often awkward | Flexible — optimizes phrasing for brevity |
| Actionability | Formulaic call-to-action | Context-sensitive framing of action |
| Novelty Handling | Poor — novelty reads as irrelevance | Better — bridges from known to adjacent |
| Linguistic Freshness | Low — same structure across exposures | High — semantic variety across exposures |
| Persuasive Appropriateness | Neutral — limited expressive range | Variable — requires explicit guardrails |

### The Three-Criterion Binding-Constraint Framework (Section 12 in v3)

All three must be true for LLM generation to be appropriate:
1. **Framing Variance** — Does content admit multiple plausible, meaningfully different framings?
2. **Linguistic Sensitivity** — Is user response sensitive to *how* (not just *whether*) relevant?
3. **Context Richness** — Does the system have sufficient grounded context for non-trivial composition?

---

## The Core Argument: WHO + WHEN + WHAT → LLM solves HOW

Modern notification systems are highly effective at deciding **who** to notify, **when** to notify, and **what** to recommend — but they remain weak at deciding **how** to communicate.

### The Pizza Example (from the paper)

The system knows:
- **WHO:** A frequent pizza buyer, 3 orders last month, prefers Italian cuisine
- **WHEN:** 12:15 PM on a Tuesday, rainy weather, hasn't opened the app in 2 days
- **WHAT:** Margherita Pizza at Tony's — $12.99, 4.8★, 25 min delivery

| Approach | Message |
|---|---|
| **Static Template (Status Quo)** | `🍕 Tony's Pizza is waiting for you! Order now.` |
| **LLM-Composed (This System)** | `Perfect rainy lunch day — Tony's Margherita is 25 min away. Your usual, rated 4.8★. 🍕` |

The LLM does not select the restaurant or the user. It composes a message that feels like it was written by someone who knows you.

---

## What This Repository Contains

| Component | Description | Language |
|---|---|---|
| **Research Paper** | Full ACM-style survey paper (PDF, LaTeX, DOCX, Slides) | — |
| **NotifyCompose SDK** | iOS Swift Package implementing signal collection + composition | Swift 5.9 |
| **Backend Server** | FastAPI server implementing all 9 pipeline components | Python 3.11 |
| **Sample iOS App** | SwiftUI app demonstrating all 3 domains + pipeline inspector | Swift / SwiftUI |

---

## Architecture

```
iOS App (Signal Collection)
        │
        │  POST /api/v1/signals  (batched, async)
        ▼
┌──────────────────────────────────────────────────────────┐
│                  NotifyCompose Server                    │
│                                                          │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │   Profile   │    │   Budget     │    │  Context   │  │
│  │   Builder   │───▶│   Router     │───▶│  Retriever │  │
│  │  (signals)  │    │ (CLV tiers)  │    │   (RAG)    │  │
│  └─────────────┘    └──────────────┘    └─────┬──────┘  │
│                                               │          │
│                          ┌────────────────────┘          │
│                          ▼                               │
│                  ┌──────────────┐                        │
│                  │   Message    │  LLM (GPT-4.1-mini)    │
│                  │   Composer   │  5 candidates          │
│                  └──────┬───────┘                        │
│                         │                                │
│                  ┌──────▼───────┐                        │
│                  │  Guardrail   │  Factuality + Policy   │
│                  │   Filter     │  Dark pattern check    │
│                  └──────┬───────┘                        │
│                         │                                │
│                  ┌──────▼───────┐                        │
│                  │   Reward     │  Pairwise ranking      │
│                  │   Ranker     │  Heuristic + LLM score │
│                  └──────┬───────┘                        │
│                         │                                │
│                  ┌──────▼───────┐                        │
│                  │    STO       │  Thompson Sampling     │
│                  │   Bandit     │  send-time optimizer   │
│                  └──────┬───────┘                        │
│                         │                                │
└─────────────────────────┼────────────────────────────────┘
                          │  ComposedNotification
                          ▼
                    iOS App (Render + Deliver)
                          │
                          │  POST /api/v1/feedback
                          ▼
                    Online Learning Loop
```

---

## Repository Structure

```
LLMNotificationComposition/
├── README.md                          ← You are here
├── ARCHITECTURE.md                    ← Full signal & API design document
├── LICENSE
│
├── docs/                              ← Research paper documents
│   ├── LLM_Notification_Composition_ACM_Paper.pdf
│   ├── LLM_Notification_Composition_ACM_Paper.tex
│   ├── LLM_Notification_Composition_Paper.docx
│   ├── LLM_Notification_Composition_Slides.pdf
│   ├── LLM_Notification_Composition_Slides.pptx
│   ├── references.bib
│   └── figures/
│       ├── fig1_prisma_literature_screening.png
│       ├── fig2_unified_pipeline.png
│       ├── fig3_domain_generalizability_matrix.png
│       └── fig4_evaluation_framework.png
│
├── server/                            ← Python FastAPI backend
│   ├── main.py                        ← App entry point
│   ├── requirements.txt
│   ├── .env.example
│   ├── models/schemas.py              ← Pydantic models
│   ├── db/database.py                 ← SQLite + SQLAlchemy
│   ├── services/
│   │   ├── profile_builder.py         ← Signal aggregation → UserProfile
│   │   ├── pipeline_services.py       ← All 7 pipeline components
│   │   └── pipeline.py                ← Orchestrator
│   ├── routes/
│   │   ├── signals.py                 ← POST /api/v1/signals
│   │   ├── compose.py                 ← POST /api/v1/compose
│   │   └── feedback.py                ← POST /api/v1/feedback
│   └── tests/test_pipeline.py
│
├── NotifyComposeSDK/                  ← iOS Swift Package
│   ├── Package.swift
│   └── Sources/NotifyCompose/
│       ├── Models/Models.swift        ← Core data types
│       ├── Core/NotifyComposeClient.swift  ← Main SDK entry point
│       ├── Signals/SignalCollector.swift   ← Batched signal tracking
│       ├── Network/NCNetworkClient.swift   ← URLSession API layer
│       └── Adapters/DomainAdapters.swift   ← Domain-specific builders
│
├── SampleApp/                         ← SwiftUI iOS sample app
│   ├── README.md
│   └── NotifyComposeSampleApp/
│       ├── App/NotifyComposeSampleApp.swift
│       └── Views/
│           ├── ContentView.swift
│           ├── FoodDeliveryDemoView.swift   ← Pizza example
│           ├── ECommerceDemoView.swift      ← Abandoned cart
│           ├── SocialMediaDemoView.swift    ← PushGen-style
│           ├── PipelineInspectorView.swift  ← Full trace view
│           └── SharedComponents.swift
│
└── src/                               ← Diagram generation scripts
    ├── draw_pipeline.py
    ├── draw_domain.py
    └── draw_evaluation.py
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- Xcode 15+ (for iOS app)

### Step 1 — Start the Backend Server

```bash
cd server
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for the interactive Swagger API documentation.

### Step 2 — Test the Pipeline via cURL

**Send a user signal:**
```bash
curl -X POST http://localhost:8000/api/v1/signals \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "signals": [
      {
        "type": "item_click",
        "item_id": "pizza_margherita",
        "category": "food/italian",
        "timestamp": "2026-03-18T12:00:00Z"
      }
    ],
    "device_context": { "timezone": "America/Los_Angeles", "locale": "en_US" }
  }'
```

**Compose the pizza notification:**
```bash
curl -X POST http://localhost:8000/api/v1/compose \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "domain": "food_delivery",
    "intent": "re_engagement",
    "content_item": {
      "item_id": "pizza_margherita",
      "title": "Margherita Pizza",
      "category": "food/italian",
      "attributes": {
        "restaurant": "Tonys Pizza",
        "price": "$12.99",
        "rating": "4.8",
        "deliveryTime": "25 min"
      }
    },
    "trigger_context": {
      "local_hour": 12,
      "day_of_week": 3,
      "weather_condition": "rainy",
      "recent_app_open": false
    },
    "options": {
      "enable_frequency_cap": true,
      "enable_guardrails": true,
      "enable_send_time_optimization": true,
      "max_candidates": 5
    }
  }'
```

**Expected response:**
```json
{
  "notification_id": "notif_a1b2c3d4",
  "title": "Perfect rainy lunch — Tony's is 25 min away 🍕",
  "body": "Your Margherita (4.8★) is ready to order. Tap to bring it home.",
  "scheduled_at": "2026-03-18T12:15:00Z",
  "composition_path": "LLM Full Pipeline",
  "reward_score": 0.87,
  "pipeline_trace": {
    "budget_decision": "LLM Full Pipeline (Gold tier)",
    "retrieved_context_keys": ["category_affinity", "order_history", "weather", "time_of_day"],
    "candidates_generated": 5,
    "guardrails_applied": [],
    "candidates_filtered": 0,
    "winning_candidate_rank": 1,
    "send_time_optimized": true,
    "latency_ms": 1240
  }
}
```

### Step 3 — iOS SDK Integration

Add the Swift Package to your Xcode project:

```
File → Add Package Dependencies → https://github.com/ndagrawal/LLMNotificationComposition
```

Select the `NotifyCompose` library target.

**Initialize (once per app session):**
```swift
import NotifyCompose

let client = NotifyComposeClient(
    baseURL: "https://your-server.com",
    userId: currentUser.id
)
```

**Track user signals (automatic batching + flush):**
```swift
// Track a product view
client.track(.screenView, itemId: "pizza_001", category: "food/italian")

// Track a purchase
client.track(.purchase, itemId: "pizza_001", category: "food/italian")
```

**Compose a notification:**
```swift
let request = FoodDeliveryAdapter.reEngagement(
    userId: currentUser.id,
    restaurantId: "rest_tonys_001",
    restaurantName: "Tony's Pizza",
    dishName: "Margherita Pizza",
    price: "$12.99",
    rating: "4.8",
    deliveryTime: "25 min",
    category: "food/italian",
    weatherCondition: "rainy"
)

let notification = try await client.compose(request: request)
print(notification.title)            // "Perfect rainy lunch — Tony's is 25 min away 🍕"
print(notification.compositionPath)  // .llmFull
print(notification.rewardScore)      // 0.87
```

**Close the feedback loop:**
```swift
await client.reportOpened(notificationId: notification.notificationId)
await client.reportConverted(notificationId: notification.notificationId)
```

### Step 4 — Run the Sample iOS App

```bash
open SampleApp/NotifyComposeSampleApp.xcodeproj
```

In Xcode: **Product → Scheme → Edit Scheme → Run → Environment Variables:**
```
NOTIFY_COMPOSE_SERVER_URL = http://localhost:8000
```

The sample app has four tabs:
- **Food** — The pizza re-engagement scenario with live weather/time controls
- **Shop** — Abandoned cart recovery with product selector and discount toggle
- **Social** — PushGen-style new content and re-engagement notifications
- **Inspector** — Full pipeline execution trace mapped to paper sections

---

## Pipeline → Paper Mapping

| Paper Section | Component | Implementation |
|---|---|---|
| §4.1 Budget Router | `BudgetRouter` | `server/services/pipeline_services.py` |
| §4.2 RAG Retrieval | `ContextRetriever` | `server/services/pipeline_services.py` |
| §4.3 PEFT/LoRA Composer | `MessageComposer` | `server/services/pipeline_services.py` |
| §4.4 Reward Ranker | `RewardRanker` | `server/services/pipeline_services.py` |
| §4.5 Guardrail Filter | `GuardrailFilter` | `server/services/pipeline_services.py` |
| §4.6 STO Bandit | `SendTimeOptimizer` | `server/services/pipeline_services.py` |
| §3.1 Signal Collection | `SignalCollector` | `NotifyComposeSDK/.../SignalCollector.swift` |
| §3.2 Profile Builder | `ProfileBuilder` | `server/services/profile_builder.py` |
| §7 Feedback Loop | Feedback handler | `server/routes/feedback.py` + `client.reportOpened()` |

---

## Domain Adapters

```swift
// Food Delivery
FoodDeliveryAdapter.reEngagement(...)   // Pizza example
FoodDeliveryAdapter.recommendation(...)
FoodDeliveryAdapter.orderUpdate(...)    // Bypasses frequency cap

// E-Commerce
ECommerceAdapter.abandonedCart(...)     // With CLV-aware urgency
ECommerceAdapter.flashSale(...)
ECommerceAdapter.recommendation(...)

// Social Media
SocialMediaAdapter.newContent(...)      // PushGen-style
SocialMediaAdapter.socialActivity(...)
SocialMediaAdapter.reEngagement(...)
```

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/signals` | POST | Ingest batched user signals |
| `/api/v1/compose` | POST | Run the full composition pipeline |
| `/api/v1/feedback` | POST | Report notification outcome (opens/conversions) |
| `/api/v1/debug/profile/{user_id}` | GET | Inspect computed user profile |
| `/docs` | GET | Interactive Swagger UI |
| `/health` | GET | Server health check |

---

## Research Paper

| Format | File |
|---|---|
| PDF (ACM Style) | [`docs/LLM_Notification_Composition_ACM_Paper.pdf`](docs/LLM_Notification_Composition_ACM_Paper.pdf) |
| LaTeX Source | [`docs/LLM_Notification_Composition_ACM_Paper.tex`](docs/LLM_Notification_Composition_ACM_Paper.tex) |
| Word Document | [`docs/LLM_Notification_Composition_Paper.docx`](docs/LLM_Notification_Composition_Paper.docx) |
| Slides (PDF) | [`docs/LLM_Notification_Composition_Slides.pdf`](docs/LLM_Notification_Composition_Slides.pdf) |
| Slides (PPTX) | [`docs/LLM_Notification_Composition_Slides.pptx`](docs/LLM_Notification_Composition_Slides.pptx) |

### Key Contributions

1. **Systematic Survey** — PRISMA-guided review of 28 primary sources (2018–2026) with three-tier evidence classification
2. **Architectural Disentanglement** — Explicit attribution matrix separating LLM contributions from adjacent systems
3. **Unified Pipeline** — End-to-end framework integrating RAG, PEFT/LoRA, reward modeling, contextual bandits, guardrails, and online learning
4. **Critical Evaluation** — Analysis of offline-online metric mismatch, causal inference challenges, and the manipulation vs. personalization boundary

### Domain Results

| Domain | System | Technology | Reported Lift | Evidence |
|---|---|---|---|---|
| Social Media | Kuaishou PushGen | SFT + Pairwise Reward | +8.0% CTR | Peer-reviewed |
| Social Media | Instagram Diversity | Diversity-Aware Bandit | +14.5% retention | Engineering blog |
| Food Delivery | DoorDash GNN | GNN + LLM | +1.0% CTR | Engineering blog |
| E-Commerce | LLM Content Optimizer | Prompt Engineering | +12% conversion | Engineering blog |

---

## Citation

```bibtex
@inproceedings{agrawal2026llmnotification,
  author    = {Agrawal, Nilesh},
  title     = {LLM-Based Intelligent Notification Composition: From Static Personalization
               to Context-Aware Persuasive Messaging},
  booktitle = {Proceedings of the ACM Web Conference},
  year      = {2026},
  address   = {Seattle, WA, USA},
  publisher = {ACM}
}
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

**Nilesh Agrawal** · Seattle, WA · [nilesh.d.agrawal@gmail.com](mailto:nilesh.d.agrawal@gmail.com) · [linkedin.com/in/nileshdagrawal](https://www.linkedin.com/in/nileshdagrawal/)
