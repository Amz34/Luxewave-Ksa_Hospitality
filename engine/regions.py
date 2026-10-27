"""
Saudi Arabia Regions & Key Municipalities matcher for B2B Hospitality Delivery.
Validates delivery destinations across all 13 Saudi Provinces.
"""
import re

REGIONS: dict[str, tuple[str, ...]] = {
    "الرياض": ("riyadh", "الرياض", "الدرعية", "الخرج", "المجمعة", "الدوادمي", "wadi ad-dawasir"),
    "مكة المكرمة": ("makkah", "mecca", "مكة", "جدة", "jeddah", "الطائف", "taif", "رابغ", "القنفذة"),
    "المدينة المنورة": ("madinah", "medina", "المدينة", "ينبع", "yanbu", "العلا", "al ula", "بدر"),
    "المنطقة الشرقية": ("eastern province", "الدمام", "dammam", "الخبر", "khobar", "الظهران", "dhahran", "الجبيل", "jubail", "الأحساء", "al ahsa", "القطيف", "حفر الباطن"),
    "عسير": ("asir", "أبها", "abha", "خميس مشيط", "khamis mushait", "بيشة", "محايل عسير"),
    "تبوك": ("tabuk", "تبوك", "نيوم", "neom", "ضباء", "الوجه", "حقل", "أملج"),
    "حائل": ("hail", "حائل", "بقعاء"),
    "الحدود الشمالية": ("northern borders", "عرعر", "arar", "طريف", "رفحاء"),
    "جازان": ("jazan", "jizan", "جازان", "صبيا", "أبو عريش", "صامطة", "فرسان"),
    "نجران": ("najran", "نجران", "شرورة"),
    "الباحة": ("al bahah", "baha", "الباحة", "بلجرشي", "المندق"),
    "الجوف": ("al jawf", "jouf", "سكاكا", "sakaka", "القريات", "طبرجل"),
    "القصيم": ("al qassim", "qassim", "بريدة", "buraidah", "عنيزة", "onaizah", "الرس"),
}

def normalize_text(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"[إأآا]", "ا", t)
    t = re.sub(r"ة", "ه", t)
    t = re.sub(r"[\s\-_]+", " ", t)
    return t

_LOOKUP: list[tuple[str, str]] = [
    (normalize_text(alias), canonical)
    for canonical, aliases in REGIONS.items()
    for alias in (canonical, *aliases)
]

def match_ksa_region(text: str) -> str | None:
    norm = normalize_text(text or "")
    if not norm:
        return None
    for alias, canonical in _LOOKUP:
        if norm == alias:
            return canonical
    for alias, canonical in _LOOKUP:
        if len(alias) >= 3 and alias in norm:
            return canonical
    return None
