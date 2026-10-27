"""
FastAPI Enterprise Microservice for Luxe Wave KSA B2B Hospitality.
Coordinates FSM agent, zero-leak pricing, KSA phone validation, rate limiting,
and instant dispatch to @AzGem_Bot.
"""
import logging
from typing import Any
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from engine.phone_normalizer import normalize_ksa_phone, format_ksa_international, KsaPhoneValidationError
from engine.regions import match_ksa_region
from engine.rate_limiter import contact_form_limiter, chat_stream_limiter
from engine.b2b_pricing_engine import calculate_b2b_quote, WHOLESALE_CATALOG
from engine.fsm_agent import HospitalityFSM, ConversationState, inspect_for_injection
from engine.telegram_notifier import dispatch_new_b2b_inquiry_alert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("luxewave.api")

app = FastAPI(
    title="Luxe Wave KSA Hospitality Engine",
    description="Enterprise B2B Automation, AI FSM Agent, and Quotation Service for Saudi Hospitality Properties",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LeadInquiryRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=8, max_length=25)
    property_name: str | None = Field(default="Hotel / Serviced Apartments")
    region: str | None = Field(default=None)
    message: str | None = Field(default="")
    source: str = Field(default="web-portal")

class QuoteItemRequest(BaseModel):
    sku: str
    quantity: int = Field(..., gt=0)

class QuoteCalculationRequest(BaseModel):
    items: list[QuoteItemRequest]
    customer_phone: str | None = None
    region: str | None = None

class ChatTurnRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1500)
    state: ConversationState = Field(default=ConversationState.DISCOVERY)
    property_name: str | None = None
    phone: str | None = None
    region: str | None = None

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "luxewave-hospitality-engine",
        "region_coverage": "All 13 KSA Provinces",
        "vat_compliance": "ZATCA 15% compliant",
        "telegram_integration": "@AzGem_Bot active"
    }

@app.get("/catalog/public")
def get_public_catalog():
    """
    Public showcase endpoint: strictly delivers zero pricing to prevent competitive leakage.
    Clients must request a quotation for volume-tiered pricing.
    """
    showcase = []
    for sku, item in WHOLESALE_CATALOG.items():
        showcase.append({
            "sku": sku,
            "name_ar": item["name_ar"],
            "name_en": item["name_en"],
            "category": item["category"],
            "moq": item["moq"],
            "price_status": "Quotation on Request (Wholesale Volume Tiers)"
        })
    return {"catalog": showcase}

@app.post("/inquiry/submit")
def submit_rfq_lead(payload: LeadInquiryRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not contact_form_limiter.hit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before submitting another RFQ."
        )

    # 1. Validate KSA Phone
    try:
        normalized_phone = normalize_ksa_phone(payload.phone)
        intl_phone = format_ksa_international(normalized_phone)
    except KsaPhoneValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 2. Match Region
    matched_region = match_ksa_region(payload.region or payload.message or "") or "الرياض (المركز الرئيسي)"

    lead_data = {
        "name": payload.name,
        "phone": normalized_phone,
        "whatsapp": intl_phone,
        "property_name": payload.property_name,
        "region": matched_region,
        "message": payload.message,
        "source": payload.source
    }

    # 3. Instant Alert to @AzGem_Bot
    dispatch_new_b2b_inquiry_alert(lead_data)

    return {
        "success": True,
        "message": "RFQ lead captured successfully. Our hospitality sales director in KSA will contact you promptly.",
        "phone_normalized": intl_phone,
        "region_assigned": matched_region
    }

@app.post("/quote/calculate")
def compute_b2b_quotation(payload: QuoteCalculationRequest):
    """Deterministic server-side quotation generation."""
    items_raw = [{"sku": it.sku, "quantity": it.quantity} for it in payload.items]
    res = calculate_b2b_quote(items_raw)
    return {
        "subtotal_net_sar": str(res.subtotal_net_sar),
        "vat_15_sar": str(res.vat_sar),
        "total_gross_sar": str(res.total_gross_sar),
        "is_valid_moq": res.is_valid_moq,
        "moq_violations": res.moq_violations,
        "line_items": [
            {
                "sku": it.sku,
                "name": it.name,
                "quantity": it.quantity,
                "unit_base_sar": str(it.unit_base_sar),
                "discount_pct": str(it.discount_pct) + "%",
                "unit_net_sar": str(it.unit_net_sar),
                "total_net_sar": str(it.total_net_sar)
            }
            for it in res.items
        ]
    }

@app.post("/chat/agent")
def chat_with_hospitality_agent(turn: ChatTurnRequest, request: Request):
    """
    Finite State Machine AI agent step. Combines anti-injection guardrails
    with state machine progression.
    """
    fsm = HospitalityFSM(current_state=turn.state)
    payload_dict = {
        "message": turn.message,
        "property_name": turn.property_name,
        "phone": turn.phone,
        "region": turn.region
    }
    next_state, reply = fsm.process_event("USER_MESSAGE", payload_dict)

    return {
        "reply": reply,
        "next_state": next_state,
        "slots": fsm.collected_slots
    }
