"""
Zero-Leak Pricing & B2B Hospitality RFQ Order Engine.
Implements the core architectural decision from Dinesh Swami & Rashed Al Awamleh frameworks:
1. Public Storefront NEVER exposes wholesale/tiered pricing in HTML or client payloads.
2. Code deterministically calculates volume-tier discounts and VAT (ZATCA 15%) on the backend.
3. The LLM NEVER invents or calculates prices.
"""
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

# Standard KSA VAT Rate
KSA_VAT_RATE = Decimal("0.15")

# Standard B2B Hospitality Product Catalog (Wholesale baseline prices in SAR, hidden from public)
WHOLESALE_CATALOG = {
    "LW-BED-001": {
        "sku": "LW-BED-001",
        "name_ar": "طقم بياضات سرير فندقية قطن مصري 300 غرزة",
        "name_en": "Luxury 300TC Egyptian Cotton Bed Linen Set",
        "category": "bed_linen",
        "base_price_sar": Decimal("185.00"),
        "moq": 20,
        "volume_tiers": [
            (100, Decimal("0.10")), # 100+ units: 10% discount
            (500, Decimal("0.18")), # 500+ units: 18% discount
            (1000, Decimal("0.25")),# 1000+ units: 25% discount
        ]
    },
    "LW-BATH-002": {
        "sku": "LW-BATH-002",
        "name_ar": "طقم مناشف فاخرة 650 جرام قطن ناعم",
        "name_en": "Hotel Luxury 650 GSM Bath Towel Set",
        "category": "bath_linen",
        "base_price_sar": Decimal("65.00"),
        "moq": 50,
        "volume_tiers": [
            (200, Decimal("0.12")),
            (1000, Decimal("0.22")),
        ]
    },
    "LW-AMEN-003": {
        "sku": "LW-AMEN-003",
        "name_ar": "مجموعة مستلزمات الضيوف الفاخرة (صديقة للبيئة)",
        "name_en": "Eco-Friendly 5-Star Guest Amenity Kit",
        "category": "guest_amenities",
        "base_price_sar": Decimal("14.50"),
        "moq": 250,
        "volume_tiers": [
            (1000, Decimal("0.15")),
            (5000, Decimal("0.25")),
        ]
    },
    "LW-SAFE-004": {
        "sku": "LW-SAFE-004",
        "name_ar": "خزنة أمانات إلكترونية رقمية للغرف",
        "name_en": "Electronic Hotel Room Safe with LED Display",
        "category": "room_essentials",
        "base_price_sar": Decimal("320.00"),
        "moq": 10,
        "volume_tiers": [
            (50, Decimal("0.10")),
            (200, Decimal("0.20")),
        ]
    }
}

@dataclass
class LineItemQuote:
    sku: str
    name: str
    quantity: int
    unit_base_sar: Decimal
    discount_pct: Decimal
    unit_net_sar: Decimal
    total_net_sar: Decimal

@dataclass
class B2BQuoteResult:
    items: list[LineItemQuote]
    subtotal_net_sar: Decimal
    vat_sar: Decimal
    total_gross_sar: Decimal
    is_valid_moq: bool
    moq_violations: list[str] = field(default_factory=list)

def calculate_b2b_quote(items_request: list[dict[str, Any]]) -> B2BQuoteResult:
    """
    Deterministically computes net pricing, volume discounts, and 15% ZATCA VAT in SAR.
    Guarantees no floating point errors using Decimal (ROUND_HALF_UP).
    """
    quotes: list[LineItemQuote] = []
    subtotal = Decimal("0.00")
    violations: list[str] = []

    for req in items_request:
        sku = req.get("sku")
        qty = int(req.get("quantity", 0))
        prod = WHOLESALE_CATALOG.get(sku)
        if not prod:
            continue

        if qty < prod["moq"]:
            violations.append(f"{prod['name_en']}: Minimum Order Quantity is {prod['moq']} (requested {qty})")

        # Determine highest qualified tier discount
        discount = Decimal("0.00")
        for tier_qty, tier_disc in prod.get("volume_tiers", []):
            if qty >= tier_qty:
                if tier_disc > discount:
                    discount = tier_disc

        unit_base = prod["base_price_sar"]
        unit_net = (unit_base * (Decimal("1.00") - discount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        line_total = (unit_net * Decimal(qty)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        subtotal += line_total
        quotes.append(LineItemQuote(
            sku=sku,
            name=prod["name_en"],
            quantity=qty,
            unit_base_sar=unit_base,
            discount_pct=discount * Decimal("100"),
            unit_net_sar=unit_net,
            total_net_sar=line_total
        ))

    vat = (subtotal * KSA_VAT_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_gross = subtotal + vat

    return B2BQuoteResult(
        items=quotes,
        subtotal_net_sar=subtotal,
        vat_sar=vat,
        total_gross_sar=total_gross,
        is_valid_moq=len(violations) == 0,
        moq_violations=violations
    )
