"""
Luxe Wave B2B Hospitality Finite State Machine (FSM) & Anti-Injection Guardrails.

States:
1. DISCOVERY: Understanding property type (Hotel, Resort, Furnished Apts), room count, and procurement needs.
2. SPECIFICATION: SKU selection, sample requests, specifications review.
3. QUOTE_GENERATION: Quantities collected, volume discount tiers evaluated, deterministic quote created.
4. COMPLIANCE_AND_CONFIRMATION: VAT (ZATCA), CR validation, delivery region confirmed.
5. HANDOFF_HUMAN: Triggered when complex negotiations, custom branding, or customer requests a human key account manager.
"""
from enum import Enum
from typing import Any
import re

class ConversationState(str, Enum):
    DISCOVERY = "DISCOVERY"
    SPECIFICATION = "SPECIFICATION"
    QUOTE_GENERATION = "QUOTE_GENERATION"
    CONFIRMED = "CONFIRMED"
    HUMAN_HANDOFF = "HUMAN_HANDOFF"
    CANCELLED = "CANCELLED"

# Forbidden prompt-injection / role-play bypass strings
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"system\s*:\s*",
    r"you\s+are\s+now\s+(an?\s+)?DAN",
    r"as\s+an\s+unrestricted\s+AI",
    r"reveal\s+(your\s+)?(system\s+prompt|instructions|secret)",
    r"act\s+as\s+a\s+linux\s+terminal",
    r"drop\s+database",
    r"<\s*script\s*>",
]

# Stiff AI / Non-Saudi expressions to avoid in high-end Saudi B2B conversations
FORBIDDEN_PHRASES = (
    "نعم يا فندم", "بالتأكيد يا باشا", "يسعدني مساعدتك يا سيدي", "عزيزي العميل",
    "بناء على رغبتك", "تفضل بالاطلاع على الأسعار التلقائية"
)

def inspect_for_injection(user_input: str) -> bool:
    """Returns True if malicious prompt injection pattern is detected."""
    normalized = user_input.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, normalized):
            return True
    return False

class HospitalityFSM:
    """Deterministic Finite State Machine managing B2B lead progression."""
    def __init__(self, current_state: ConversationState = ConversationState.DISCOVERY):
        self.state = current_state
        self.collected_slots: dict[str, Any] = {
            "property_name": None,
            "property_type": None,
            "region": None,
            "contact_name": None,
            "phone": None,
            "requested_items": [],
            "human_requested": False
        }

    def process_event(self, event: str, payload: dict[str, Any]) -> tuple[ConversationState, str]:
        """
        Transitions states based on deterministic business rules rather than hallucinated LLM logic.
        """
        # Guardrail check
        text = payload.get("message", "")
        if inspect_for_injection(text):
            return self.state, "نعتذر، لا يمكن معالجة هذا الطلب. نرحب باستفساراتكم حول توريدات الفنادق والضيافة."

        # Check for human request
        if any(w in text.lower() for w in ["انسان", "مندوب", "مسؤول المبيعات", "human", "agent", "talk to human"]):
            self.state = ConversationState.HUMAN_HANDOFF
            self.collected_slots["human_requested"] = True
            return self.state, "تم تحويل طلبكم فوراً إلى مدير الحسابات الميداني في الرياض. سيتواصل معكم خلال دقائق عبر واتساب."

        if self.state == ConversationState.DISCOVERY:
            if payload.get("property_name") or payload.get("property_type"):
                self.collected_slots["property_name"] = payload.get("property_name")
                self.collected_slots["property_type"] = payload.get("property_type")
                self.state = ConversationState.SPECIFICATION
                return self.state, "أهلاً وسهلاً بكم في لوكس ويف. يسعدنا توريد متطلباتكم الفندقية الفاخرة. ما هي الفئات أو المنتجات التي ترغبون في تسعيرها أو طلب عينات لها؟"

        elif self.state == ConversationState.SPECIFICATION:
            items = payload.get("items", [])
            if items:
                self.collected_slots["requested_items"] = items
                self.state = ConversationState.QUOTE_GENERATION
                return self.state, "تم تسجيل المنتجات المطلوبة. يرجى تزويدنا بالكميات التقديرية واسم المنشأة والمدينة لتطبيق خصومات التوريد المعتمدة وتجهيز عرض السعر الرسمي."

        elif self.state == ConversationState.QUOTE_GENERATION:
            if payload.get("phone") and payload.get("region"):
                self.collected_slots["phone"] = payload.get("phone")
                self.collected_slots["region"] = payload.get("region")
                self.state = ConversationState.CONFIRMED
                return self.state, "تم اعتماد طلب عرض السعر بنجاح وجاري إرسال مسودة العرض الرسمية مع شهادات الجودة والمطابقة SASO / SFDA."

        return self.state, "نحن بخدمتكم في لوكس ويف لتجهيز الفنادق والمنتجعات والشقق المخدومة بأعلى معايير الضيافة السعودية."
