# NotifyCompose Sample App

A SwiftUI iOS application demonstrating the **NotifyCompose SDK** across all three domains from the research paper.

## Screens

| Tab | Domain | Scenario |
|---|---|---|
| **Food** | Food Delivery | Pizza re-engagement with weather + time context |
| **Shop** | E-Commerce | Abandoned cart recovery with CLV-aware urgency |
| **Social** | Social Media | New content / social activity / re-engagement |
| **Inspector** | All | Full pipeline trace mapped to paper architecture |

## Requirements

- Xcode 15+
- iOS 16+ Simulator or device
- Python 3.11+ (for the backend server)
- OpenAI API key

## Quick Start

### 1. Start the Backend Server

```bash
cd ../server
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Open in Xcode

```bash
open NotifyComposeSampleApp.xcodeproj
```

Or open the folder in Xcode and select the `NotifyComposeSampleApp` scheme.

### 3. Configure Server URL

The app reads the server URL from the `NOTIFY_COMPOSE_SERVER_URL` environment variable.
Set it in the Xcode scheme (Product → Scheme → Edit Scheme → Run → Environment Variables):

```
NOTIFY_COMPOSE_SERVER_URL = http://localhost:8000
```

For a device on the same network, use your Mac's local IP:
```
NOTIFY_COMPOSE_SERVER_URL = http://192.168.1.x:8000
```

### 4. Run

Select a simulator (iPhone 15 Pro recommended) and press **⌘R**.

## Pipeline Inspector

The **Inspector** tab shows the full execution trace of the last composed notification, with each step mapped to the corresponding section of the research paper:

- Step 1 → Budget Router (§4.1)
- Step 2 → RAG Context Retrieval (§4.2)
- Step 3 → LLM Message Generation (§4.3)
- Step 4 → Guardrail Filter (§4.5)
- Step 5 → Reward Ranker (§4.4)
- Step 6 → Send-Time Optimization (§4.6)
