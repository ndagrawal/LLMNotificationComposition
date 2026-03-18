# NotifyCompose — System Architecture

## The Core Design Question: How Does the System Know About the User?

The paper's pipeline requires rich user signals to compose context-aware messages. This document defines exactly **where signals come from**, **how they flow**, and **how every component connects end-to-end**.

---

## Signal Sources: Three Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                        SIGNAL SOURCES                           │
│                                                                 │
│  Layer 1: iOS SDK (on-device)                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  NCSignalTracker  — passive event capture                │  │
│  │  • Screen views (which screens, dwell time)              │  │
│  │  • Taps, scrolls, purchases, shares, dismissals          │  │
│  │  • App foreground/background transitions                 │  │
│  │  • Notification open / dismiss / conversion events       │  │
│  │  • Device context: timezone, locale, network type        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │ batched HTTPS POST every 30s       │
│                            ▼                                    │
│  Layer 2: Server-Side Event Store                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  /api/v1/signals  (FastAPI endpoint)                     │  │
│  │  • Writes to SQLite (dev) / PostgreSQL (prod)            │  │
│  │  • Computes rolling aggregates per user:                 │  │
│  │    - Category affinity scores (exponential decay)        │  │
│  │    - Notification open rate (last 30 days)               │  │
│  │    - Preferred send-time histogram (STO bandit state)    │  │
│  │    - CLV tier (computed from purchase history)           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Layer 3: App-Provided Context (at request time)               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  NotificationRequest (Swift struct / JSON body)          │  │
│  │  • contentItem: what to promote (id, title, category)    │  │
│  │  • intent: re-engagement / abandoned-cart / flash-sale   │  │
│  │  • triggerContext: local hour, weather, recent app open  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## End-to-End Flow

```
iOS App                     NotifyCompose SDK              Backend Server
   │                               │                            │
   │── NCSignalTracker.track() ───►│                            │
   │   (every user action)         │── POST /api/v1/signals ──►│
   │                               │   (batched, 30s)           │── store + aggregate
   │                               │                            │
   │── compose(request) ──────────►│                            │
   │   (trigger: push needed)      │── POST /api/v1/compose ──►│
   │                               │                            │── 1. fetch user profile
   │                               │                            │── 2. BudgetRouter (CLV)
   │                               │                            │── 3. ContextRetriever (RAG)
   │                               │                            │── 4. MessageComposer (LLM)
   │                               │                            │── 5. GuardrailFilter
   │                               │                            │── 6. RewardRanker
   │                               │                            │── 7. FrequencyCapper
   │                               │                            │── 8. SendTimeOptimizer
   │                               │◄── ComposedNotification ───│
   │◄── ComposedNotification ──────│                            │
   │                               │                            │
   │── scheduleNotification() ────►│                            │
   │   (UNUserNotificationCenter)  │                            │
   │                               │                            │
   │── NCSignalTracker.track(      │                            │
   │     .notificationOpened) ────►│── POST /api/v1/signals ──►│── update STO bandit
   │                               │                            │── update reward model
```

---

## Component Responsibilities

### iOS SDK (`NotifyCompose` Swift Package)

| Component | File | Responsibility |
|---|---|---|
| `NCSignalTracker` | `SignalTracker.swift` | Captures all user events, batches and POSTs to `/signals` |
| `NCNotifyComposeClient` | `APIClient.swift` | Calls `/compose` endpoint, returns `ComposedNotification` |
| `NCNotificationScheduler` | `NotificationScheduler.swift` | Schedules via `UNUserNotificationCenter` at the STO time |
| `NCFeedbackReporter` | `FeedbackReporter.swift` | Reports open/dismiss/convert events back to server |
| Models | `Models.swift` | `UserSignal`, `NotificationRequest`, `ComposedNotification` |
| Domain Adapters | `Adapters/` | `SocialMediaAdapter`, `FoodDeliveryAdapter`, `ECommerceAdapter` |

### Backend Server (`server/` Python FastAPI)

| Component | File | Responsibility |
|---|---|---|
| Signal Ingestion | `routes/signals.py` | Receives batched signals, writes to DB, triggers aggregation |
| User Profile Builder | `services/profile_builder.py` | Aggregates signals into `UserProfile` (CLV, affinities, history) |
| Budget Router | `services/budget_router.py` | Maps CLV tier → composition path |
| Context Retriever | `services/context_retriever.py` | RAG: fetches top-k relevant items from content store |
| Message Composer | `services/message_composer.py` | Calls OpenAI API to generate N candidate messages |
| Guardrail Filter | `services/guardrail_filter.py` | Blocks hallucinations, false urgency, prohibited patterns |
| Reward Ranker | `services/reward_ranker.py` | Scores candidates; selects winner |
| Frequency Capper | `services/frequency_capper.py` | Enforces max-touch rules per user |
| STO Optimizer | `services/sto_optimizer.py` | Thompson Sampling bandit for send-time |
| Pipeline Orchestrator | `services/pipeline.py` | Wires all components; returns `ComposedNotification` |
| Compose Route | `routes/compose.py` | `POST /api/v1/compose` endpoint |
| Feedback Route | `routes/feedback.py` | `POST /api/v1/feedback` — updates bandit & reward model |

---

## API Contract

### `POST /api/v1/signals`
Batched signal ingestion from the iOS SDK.

```json
{
  "userId": "user_abc123",
  "signals": [
    {
      "type": "screen_view",
      "itemId": "pizza_margherita",
      "category": "food/italian",
      "durationSeconds": 12.4,
      "timestamp": "2026-03-18T18:30:00Z"
    },
    {
      "type": "purchase",
      "itemId": "pizza_margherita",
      "category": "food/italian",
      "timestamp": "2026-03-18T18:31:00Z"
    }
  ],
  "deviceContext": {
    "timezone": "America/Los_Angeles",
    "locale": "en_US",
    "networkType": "wifi"
  }
}
```

**Response:** `{ "status": "ok", "signalsIngested": 2 }`

---

### `POST /api/v1/compose`
Request a composed notification for a user.

```json
{
  "userId": "user_abc123",
  "domain": "food_delivery",
  "intent": "re_engagement",
  "contentItem": {
    "itemId": "pizza_margherita",
    "title": "Margherita Pizza",
    "category": "food/italian",
    "attributes": {
      "price": "$12.99",
      "rating": "4.8",
      "deliveryTime": "25 min",
      "restaurant": "Tony's Pizza"
    }
  },
  "triggerContext": {
    "localHour": 18,
    "dayOfWeek": 3,
    "weatherCondition": "rainy",
    "recentAppOpen": false
  },
  "options": {
    "maxCandidates": 5,
    "maxTitleLength": 50,
    "maxBodyLength": 120,
    "enableGuardrails": true,
    "enableFrequencyCap": true,
    "enableSendTimeOptimization": true
  }
}
```

**Response:**
```json
{
  "notificationId": "notif_xyz789",
  "title": "Rainy evening? Tony's Margherita is 25 min away 🍕",
  "body": "Your go-to Italian spot has a 4.8-star special tonight. Order now and get it before the rain picks up.",
  "scheduledAt": "2026-03-18T18:45:00Z",
  "compositionPath": "LLM Full Pipeline",
  "rewardScore": 0.87,
  "pipelineTrace": {
    "budgetDecision": "CLV=platinum → LLM Full Pipeline",
    "retrievedContextKeys": ["preference:food/italian", "history:pizza_margherita", "context:weather:rainy"],
    "candidatesGenerated": 5,
    "guardrailsApplied": ["length_check", "urgency_check"],
    "candidatesFiltered": 1,
    "winningCandidateRank": 2,
    "sendTimeOptimized": true,
    "latencyMs": 1240
  }
}
```

---

### `POST /api/v1/feedback`
Report notification outcome back to the server (updates STO bandit + reward model).

```json
{
  "notificationId": "notif_xyz789",
  "userId": "user_abc123",
  "outcome": "converted",
  "openedAt": "2026-03-18T18:47:00Z",
  "convertedAt": "2026-03-18T18:49:00Z"
}
```

**Outcome values:** `"opened"` | `"dismissed"` | `"converted"` | `"unsubscribed"`

---

## Signal Types Tracked by iOS SDK

| Signal Type | When Fired | Used For |
|---|---|---|
| `screen_view` | User opens a screen | Category affinity, dwell time |
| `item_click` | User taps an item | Preference scoring |
| `purchase` | Checkout completed | CLV calculation, category affinity |
| `share` | User shares content | High-engagement signal |
| `save` | User saves/bookmarks | Intent signal |
| `dismiss` | User swipes away content | Negative signal |
| `app_foreground` | App becomes active | Active hours histogram |
| `app_background` | App goes to background | Session length |
| `notification_received` | Push delivered | Delivery confirmation |
| `notification_opened` | User taps notification | CTR signal → STO bandit reward |
| `notification_dismissed` | User swipes notification | Negative CTR → STO bandit penalty |
| `notification_converted` | Action completed after open | Conversion signal → reward model |

---

## CLV Tier Computation (Server-Side)

```
CLV Score = (purchase_count × avg_order_value × recency_weight) / cohort_percentile

Tier Assignment:
  platinum : CLV percentile ≥ 95
  gold     : CLV percentile ≥ 80
  silver   : CLV percentile ≥ 50
  bronze   : CLV percentile < 50
```

## Category Affinity Score (Server-Side)

Exponential time-decay over interaction history:

```
affinity(category) = Σ weight(action_type) × exp(-λ × days_since_interaction)

action weights: purchase=1.0, save=0.6, click=0.4, view=0.2, dismiss=-0.3
decay rate λ = 0.1 (half-life ≈ 7 days)
```

---

## Local Development Setup

See [`server/README.md`](./server/README.md) for the complete setup guide.

**Quick start:**
```bash
cd server
pip install -r requirements.txt
cp .env.example .env          # add your OPENAI_API_KEY
python -m uvicorn main:app --reload --port 8000
```

The iOS sample app points to `http://localhost:8000` by default (configurable in `SampleApp/Config.swift`).
