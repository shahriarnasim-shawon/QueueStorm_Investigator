import google.generativeai as genai
import json
import os
import re
from dotenv import load_dotenv
from models import TicketRequest, TicketResponse
from prompts import SYSTEM_PROMPT

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel(
    model_name="gemini-3.1-flash-lite",
    system_instruction=SYSTEM_PROMPT,
    generation_config=genai.GenerationConfig(
        temperature=0.1,  # low temperature = consistent, deterministic outputs
        max_output_tokens=1024,
    )
)

def build_user_message(ticket: TicketRequest) -> str:
    txn_block = "No transaction history provided."
    if ticket.transaction_history:
        lines = []
        for t in ticket.transaction_history:
            lines.append(
                f"- ID: {t.transaction_id} | {t.timestamp} | Type: {t.type} | "
                f"Amount: {t.amount} BDT | To/From: {t.counterparty} | Status: {t.status}"
            )
        txn_block = "\n".join(lines)
    
    return f"""TICKET ID: {ticket.ticket_id}
CHANNEL: {ticket.channel or 'unknown'}
USER TYPE: {ticket.user_type or 'unknown'}
LANGUAGE: {ticket.language or 'unknown'}
CAMPAIGN: {ticket.campaign_context or 'none'}

CUSTOMER COMPLAINT:
{ticket.complaint}

RECENT TRANSACTION HISTORY:
{txn_block}

Investigate this ticket and return ONLY the required JSON response."""

async def analyze_ticket(ticket: TicketRequest) -> TicketResponse:
    user_message = build_user_message(ticket)
    
    response = model.generate_content(user_message)
    raw_text = response.text.strip()
    
    # Strip markdown code fences if model adds them
    raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text)
    raw_text = re.sub(r'\s*```$', '', raw_text)
    raw_text = raw_text.strip()
    
    data = json.loads(raw_text)
    
    # Force ticket_id to match input (safety override)
    data["ticket_id"] = ticket.ticket_id
    
    # Safety post-processing: scan customer_reply for violations
    data = safety_post_process(data)
    
    return TicketResponse(**data)

def safety_post_process(data: dict) -> dict:
    """Last-line-of-defense safety checks after LLM response"""
    reply = data.get("customer_reply", "").lower()
    
    # Check for credential requests
    forbidden_phrases = ["your pin", "your otp", "your password", "otp bolen", "pin bolen", 
                         "share your pin", "share your otp", "enter your otp", "verify with otp"]
    for phrase in forbidden_phrases:
        if phrase in reply:
            data["customer_reply"] = (
                "We have received your request and our team will review it shortly. "
                "Please do not share your PIN or OTP with anyone. "
                "We will contact you through official support channels."
            )
            data["human_review_required"] = True
            break
    
    # Check for unauthorized refund promises
    promise_phrases = ["we will refund", "will be refunded", "আমরা ফেরত দেব", "টাকা ফেরত দেওয়া হবে",
                       "you will receive", "we will transfer back", "we will send back"]
    for phrase in promise_phrases:
        if phrase in reply:
            data["customer_reply"] = data["customer_reply"].replace(
                phrase, "any eligible amount will be returned through official channels"
            )
            break
    
    return data
