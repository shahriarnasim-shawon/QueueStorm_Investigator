from pydantic import BaseModel
from typing import Literal, Optional, List

class TransactionEntry(BaseModel):
    transaction_id: str
    timestamp: str
    type: Literal["transfer", "payment", "cash_in", "cash_out", "settlement", "refund"]
    amount: float
    counterparty: str
    status: Literal["completed", "failed", "pending", "reversed"]

class TicketRequest(BaseModel):
    ticket_id: str
    complaint: str
    language: Optional[str] = None  # "en", "bn", "mixed"
    channel: Optional[str] = None
    user_type: Optional[str] = None
    campaign_context: Optional[str] = None
    transaction_history: Optional[List[TransactionEntry]] = []
    metadata: Optional[dict] = None

class TicketResponse(BaseModel):
    ticket_id: str
    relevant_transaction_id: Optional[str]  # str or null
    evidence_verdict: Literal["consistent", "inconsistent", "insufficient_data"]
    case_type: Literal["wrong_transfer", "payment_failed", "refund_request", "duplicate_payment", "merchant_settlement_delay", "agent_cash_in_issue", "phishing_or_social_engineering", "other"]
    severity: Literal["low", "medium", "high", "critical"]
    department: Literal["customer_support", "dispute_resolution", "payments_ops", "merchant_operations", "agent_operations", "fraud_risk"]
    agent_summary: str
    recommended_next_action: str
    customer_reply: str
    human_review_required: bool
    confidence: Optional[float] = None
    reason_codes: Optional[List[str]] = None
