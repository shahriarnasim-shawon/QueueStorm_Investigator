# QueueStorm Investigator

An AI-powered fintech support ticket analysis API for the SUST CSE Carnival 2026 Codex Community Hackathon. 

This service acts as an internal AI copilot for support agents (e.g., at mobile financial platforms like bKash). It analyzes digital finance complaints by intelligently cross-referencing customer transaction history and determining the nature of the issue.

## 1. Project Overview
QueueStorm Investigator solves the challenge of manually reviewing massive volumes of support tickets. 
By integrating the `gemini-3.1-flash-lite` model, it categorizes tickets, assesses case severities, reasons over provided transactional evidence, handles multi-lingual queries (e.g., English and Bangla), and drafts a compliant initial response to the user.

## 2. Setup & Run Instructions

### Local Setup
1. Clone this repository:
   ```bash
   git clone https://github.com/shahriarnasim-shawon/QueueStorm_Investigator
   cd queuestorm-investigator
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   Copy `.env.example` to `.env` and set your `GEMINI_API_KEY`.
   ```bash
   cp .env.example .env
   ```
5. Run the server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Deployment to Render
1. Push this code to a PUBLIC GitHub repo named `queuestorm-investigator`.
2. Go to Render.com -> New -> Web Service -> connect your GitHub repo.
3. Configure settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**: Add `GEMINI_API_KEY=<your_key>`
4. Deploy and wait for the build to finish. Test the `/health` endpoint to ensure successful deployment.

## 3. API Endpoints

### `GET /health`
Returns system status.
```bash
curl https://queuestorm-investigator-htj8.onrender.com/health
```

### `POST /analyze-ticket`
Analyzes a support ticket and returns investigation results.
```bash
curl -X POST https://queuestorm-investigator-htj8.onrender.com/analyze-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id":"TKT-001",
    "complaint":"I sent 5000 taka to a wrong number around 2pm today.",
    "language":"en",
    "channel":"in_app_chat",
    "user_type":"customer",
    "transaction_history":[
      {
        "transaction_id":"TXN-9101",
        "timestamp":"2026-04-14T14:08:22Z",
        "type":"transfer",
        "amount":5000,
        "counterparty":"+8801719876543",
        "status":"completed"
      }
    ]
  }'
```

## 4. Models Used
**Model Chosen:** `gemini-3.1-flash-lite`
**Reasoning:**
- **Speed:** Super fast latency (<5s), ideal for an operations copilot.
- **Cost:** Exceptional free tier scaling for high-volume support channels.
- **Capabilities:** Solid multilingual comprehension (handles Bangla and English context fluently).

## 5. AI Approach
We prompt Gemini with a strict persona (QueueStorm Investigator) to do reasoning and output a structured JSON response. 
The system prompt contains explicit guardrails about the allowed values (enums) and ensures that we only ever get the structural format our backend needs, avoiding markdown and extraneous text.

## 6. Evidence Reasoning Logic
The LLM applies reasoning to match the complaint with the transactions:
- **Consistent Evidence:** When transaction data matches the user's claims (amount, time, party).
- **Inconsistent Evidence:** When data blatantly contradicts the user's claims (e.g. wrong transfer but previously sent money to same party multiple times).
- **Insufficient Data:** Empty history or ambiguous matches.

## 7. Safety Logic
Safety is enforced through strict system prompts and a backend post-processing fallback mechanism. 
1. **No Credentials:** The AI must never ask for PIN, OTP, or password.
2. **No False Promises:** Refunds or reversals cannot be promised; must use official channel redirect phrasing.
3. **No Third-Party Redirects:** Support is always within official channels.
4. **Prompt Injection Defense:** If prompt injection is detected, it is immediately handled as an "other" case needing human review.

*The backend includes a `safety_post_process` loop that scans generated responses and rewrites unsafe clauses (like refund promises or OTP requests).*

## 8. Known Limitations
- Ambiguous multi-match scenarios may result in a `null` `relevant_transaction_id` requiring human intervention.
- The model might misinterpret highly complex "Banglish" terms without further specific finetuning.
- Render free tier rate limits (spin down on idle may cause initial cold-start delays).

## 9. Tech Stack
- **Language:** Python 3.11+
- **Framework:** FastAPI, Uvicorn
- **LLM Interface:** google-generativeai, pydantic
- **Deployment:** Render

## 10. Sample Request and Response

**Request:**
```json
{
  "ticket_id":"TKT-001",
  "complaint":"I sent 5000 taka to a wrong number around 2pm today.",
  "language":"en",
  "channel":"in_app_chat",
  "user_type":"customer",
  "transaction_history":[
    {
      "transaction_id":"TXN-9101",
      "timestamp":"2026-04-14T14:08:22Z",
      "type":"transfer",
      "amount":5000,
      "counterparty":"+8801719876543",
      "status":"completed"
    }
  ]
}
```

**Response:**
```json
{
  "ticket_id": "TKT-001",
  "relevant_transaction_id": "TXN-9101",
  "evidence_verdict": "consistent",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "Customer reports a wrong transfer of 5000 BDT. The transaction history confirms a completed transfer of 5000 BDT to +8801719876543 at the reported time.",
  "recommended_next_action": "Contact the recipient (+8801719876543) to initiate a reversal request.",
  "customer_reply": "We have noted your concern about transaction TXN-9101. Our team will review and any eligible amount will be returned through official channels. Please do not share your PIN or OTP with anyone.",
  "human_review_required": true,
  "confidence": 0.95,
  "reason_codes": [
    "wrong_transfer",
    "amount_match",
    "time_match"
  ]
}
```
