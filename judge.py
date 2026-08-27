"""
judge.py — Çıktı ayrıştırıcılar ve LLM-as-judge değerlendiricileri.

İki tür değerlendirme vardır:
1) Deterministik ayrıştırma: Deney 1 ve 4'te model yanıtının sonundaki
   "NİHAİ KARAR:" satırı düzenli ifadeyle okunur. Serbest metin yerine
   zorunlu karar satırı istenmesinin nedeni, değerlendirmenin kendisinin
   ikinci bir yorum katmanına dönüşmesini engellemektir.
2) LLM-as-judge: Deney 2 (gerekçe örtüşmesi/halüsinasyon) ve Deney 5
   (Ω bileşen puanları) nitel değerlendirme gerektirir; yargıç modeli
   ayrı bir API çağrısıyla, SADECE JSON dönecek şekilde çalıştırılır.
   Yargıç modelinin test edilen modelden FARKLI olması önerilir
   (kendi kendini puanlama yanlılığını azaltmak için).
"""

from __future__ import annotations

import re

import prompts
from llm_client import LLMClient, parse_json_response


# ---------------------------------------------------------------------------
# Deterministik ayrıştırıcılar
# ---------------------------------------------------------------------------
_TR_TABLO = str.maketrans("şŞıİğĞüÜöÖçÇ", "sSiIgGuUoOcC")


def _normalize(s: str) -> str:
    """Türkçe karakterleri ASCII'ye indirger ve büyük harfe çevirir."""
    return s.translate(_TR_TABLO).upper()


def nihai_karar_ayikla(metin: str, pozitif: str, negatif: str) -> str | None:
    """
    'NİHAİ KARAR: X' satırından kararı okur. Bulunamazsa son çare olarak
    tüm metinde arama yapar; yine bulunamazsa None (değerlendirme dışı).
    Karşılaştırma Türkçe karakterlerden bağımsızdır (Ş≡S, İ≡I vb.).
    """
    m = re.search(r"N[İIii]HA[İIii]\s*KARAR\s*:?\s*\[?\s*([^\]\n]+)",
                  _normalize(metin), re.IGNORECASE)
    aday = m.group(1).strip() if m else _normalize(metin)
    poz = _normalize(pozitif.replace("_", " "))
    neg = _normalize(negatif.replace("_", " "))
    # Negatif etiket pozitifin alt dizesi olabilir (KAPSAMDA / KAPSAM DIŞI
    # değil ama ŞART UYGULANIR / ŞART UYGULANMAZ öyledir) → önce negatif.
    if neg in aday:
        return negatif
    if poz in aday:
        return pozitif
    return None


# ---------------------------------------------------------------------------
# LLM-as-judge sarmalayıcıları
# ---------------------------------------------------------------------------
def rag_yargici(judge_client: LLMClient, model_yaniti: str,
                gercek_gerekce: str) -> dict:
    user = (f"MODELİN AMAÇ TESPİTİ:\n{model_yaniti}\n\n"
            f"GERÇEK GEREKÇE:\n{gercek_gerekce}")
    resp = judge_client.complete(prompts.RAG_YARGIC_SISTEM, user)
    try:
        return parse_json_response(resp.text)
    except Exception:  # noqa: BLE001
        return {"ortusme": None, "haluinasyon": None, "hata": resp.text[:200]}


def omega_bilesen_puani(judge_client: LLMClient, bilesen: str,
                        olay: str) -> dict:
    tanim = prompts.OMEGA_BILESEN_TANIMLARI[bilesen]
    system = prompts.OMEGA_YARGIC_SISTEM.format(tanim=tanim)
    resp = judge_client.complete(system, f"OLAY:\n{olay}")
    try:
        d = parse_json_response(resp.text)
        d["puan"] = max(0.0, min(1.0, float(d["puan"])))
        return d
    except Exception:  # noqa: BLE001
        return {"puan": None, "hata": resp.text[:200]}


def f_yargici(judge_client: LLMClient, olay: str) -> dict:
    resp = judge_client.complete(prompts.F_YARGIC_SISTEM, f"OLAY:\n{olay}")
    try:
        d = parse_json_response(resp.text)
        d["F"] = 1 if str(d.get("karar", "")).upper().startswith("UYGULANIR") else 0
        return d
    except Exception:  # noqa: BLE001
        return {"F": None, "hata": resp.text[:200]}
