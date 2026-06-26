from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import traceback
import os
from models import TicketRequest, TicketResponse
from analyzer import analyze_ticket

app = FastAPI(title="QueueStorm Investigator", version="1.0.0")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/analyze-ticket", response_model=TicketResponse)
async def analyze(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
    
    try:
        ticket = TicketRequest(**body)
    except ValidationError as e:
        return JSONResponse(status_code=400, content={"error": "Schema validation failed", "details": str(e)})
    
    if not ticket.complaint or not ticket.complaint.strip():
        return JSONResponse(status_code=422, content={"error": "complaint field cannot be empty"})
    
    try:
        result = await analyze_ticket(ticket)
        return result
    except Exception as e:
        # Never expose stack traces or secrets
        return JSONResponse(status_code=500, content={"error": "Internal analysis error. Please try again."})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
