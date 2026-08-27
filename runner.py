"""
runner.py — Makale 1 davranışsal doğrulama deneylerinin ana koşucusu.

API anahtarları: paket kök dizinindeki `anahtarlar.env` dosyası varsa
otomatik yüklenir (bkz. anahtarlar.env.example). Ortam değişkeni zaten
tanımlıysa dosyadaki değer ONU EZMEZ.

Kullanım örnekleri:
    # Boru hattı testi (API anahtarı gerekmez, bilimsel sonuç üretmez):
    python runner.py --deney hepsi --mock --tekrar 3

    # Gerçek koşu (Anthropic):
    python runner.py --deney 1 --provider anthropic \
        --model claude-sonnet-4-6 --tekrar 10

    # Gerçek koşu (Gemini):
    python runner.py --deney hepsi --provider gemini \
        --model gemini-3.1-pro-preview --tekrar 10

    # Yargıcı test edilen modelden ayırma (önerilir):
    python runner.py --deney 5 --provider openai --model gpt-4o \
        --judge-provider anthropic --judge-model claude-sonnet-4-6

    # Üç model ailesinde arka arkaya koşu için: bash tum_modeller.sh

Sonuçlar results/ altına JSONL olarak kaydedilir; rapor için:
    python report.py results/<dosya>.jsonl
Çok modelli çapraz rapor için:
    python capraz_rapor.py results/*.jsonl
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

import judge
import prompts
from llm_client import LLMClient, SAGLAYICILAR, parse_json_response
from rag import Retriever, kaynaklari_bicimlendir

PAKET_DIZINI = os.path.dirname(os.path.abspath(__file__))
SENARYO_DIZINI = os.path.join(PAKET_DIZINI, "scenarios")
SONUC_DIZINI = os.path.join(PAKET_DIZINI, "results")
ANAHTAR_DOSYASI = os.path.join(PAKET_DIZINI, "anahtarlar.env")


def anahtarlari_yukle():
    """anahtarlar.env varsa KEY=VALUE satırlarını ortama yükler.

    Mevcut ortam değişkenlerini ezmez; # ile başlayan satırları atlar.
    """
    if not os.path.exists(ANAHTAR_DOSYASI):
        return
    with open(ANAHTAR_DOSYASI, encoding="utf-8") as f:
        for satir in f:
            satir = satir.strip()
            if not satir or satir.startswith("#") or "=" not in satir:
                continue
            ad, deger = satir.split("=", 1)
            ad, deger = ad.strip(), deger.strip().strip('"').strip("'")
            if ad and deger and ad not in os.environ:
                os.environ[ad] = deger


def yukle(ad: str) -> dict:
    with open(os.path.join(SENARYO_DIZINI, ad), encoding="utf-8") as f:
        return json.load(f)


class SonucYazici:
    def __init__(self, etiket: str):
        os.makedirs(SONUC_DIZINI, exist_ok=True)
        zaman = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.yol = os.path.join(SONUC_DIZINI, f"{etiket}_{zaman}.jsonl")
        self._f = open(self.yol, "a", encoding="utf-8")

    def yaz(self, kayit: dict):
        self._f.write(json.dumps(kayit, ensure_ascii=False) + "\n")
        self._f.flush()

    def kapat(self):
        self._f.close()


# ===========================================================================
# Deney 1 — Normlar hiyerarşisi düzeltmesi
# ===========================================================================
def deney1(client: LLMClient, tekrar: int, yazici: SonucYazici):
    veri = yukle("deney1_hiyerarsi.json")
    konfigler = {
        "V_baseline": prompts.TEMEL_ROL,
        "V_hiyerarsi": prompts.TEMEL_ROL + prompts.MODUL_HIYERARSI,
    }
    for s in veri["senaryolar"]:
        dogru = s.get("dogru_cevap_etiketi", veri["dogru_cevap_etiketi"])
        user = prompts.DENEY1_SORU_SABLONU.format(
            kanun=s["kanun"], teblig=s["teblig"], olay=s["olay"], soru=s["soru"])
        for konfig, system in konfigler.items():
            for t in range(tekrar):
                resp = client.complete(system, user)
                karar = judge.nihai_karar_ayikla(
                    resp.text, "SART_UYGULANIR", "SART_UYGULANMAZ")
                yazici.yaz({
                    "deney": "deney1", "senaryo": s["id"], "konfig": konfig,
                    "tekrar": t, "kontrol": s.get("kontrol", False),
                    "karar": karar, "dogru_cevap": dogru,
                    "dogru_mu": (karar == dogru) if karar else None,
                    "model": resp.model, "provider": resp.provider,
                    "yanit": resp.text,
                })
                print(f"  [D1] {s['id']} {konfig} #{t}: {karar} "
                      f"({'✓' if karar == dogru else '✗'})")


# ===========================================================================
# Deney 2 — RAG (tarihi amaçsal yorum)
# ===========================================================================
def deney2(client: LLMClient, judge_client: LLMClient, tekrar: int,
           yazici: SonucYazici, retriever_yontem: str):
    veri = yukle("deney2_rag.json")
    retriever = Retriever(veri["korpus"], yontem=retriever_yontem)
    for s in veri["senaryolar"]:
        for konfig in ("V_ragsiz", "V_ragli"):
            if konfig == "V_ragli":
                belgeler = retriever.getir(s["soru"], k=2)
                user = prompts.DENEY2_SORU_SABLONU_RAGLI.format(
                    kaynaklar=kaynaklari_bicimlendir(belgeler), soru=s["soru"])
                erisim = [d["belge_id"] for d in belgeler]
            else:
                user = prompts.DENEY2_SORU_SABLONU_RAGSIZ.format(soru=s["soru"])
                erisim = []
            for t in range(tekrar):
                resp = client.complete(prompts.TEMEL_ROL, user)
                degerlendirme = judge.rag_yargici(
                    judge_client, resp.text, s["gercek_gerekce"])
                yazici.yaz({
                    "deney": "deney2", "senaryo": s["id"], "konfig": konfig,
                    "tekrar": t, "erisilen_belgeler": erisim,
                    "ortusme": degerlendirme.get("ortusme"),
                    "haluinasyon": degerlendirme.get("haluinasyon"),
                    "tuzak": s.get("tuzak"),
                    "model": resp.model, "provider": resp.provider,
                    "yanit": resp.text,
                    "yargic_gerekce": degerlendirme.get("gerekce"),
                })
                print(f"  [D2] {s['id']} {konfig} #{t}: "
                      f"örtüşme={degerlendirme.get('ortusme')} "
                      f"halüsinasyon={degerlendirme.get('haluinasyon')}")


# ===========================================================================
# Deney 3 — Anayasal kısıt ajanı
# ===========================================================================
def deney3(client: LLMClient, tekrar: int, yazici: SonucYazici):
    veri = yukle("deney3_kisit.json")
    konfigler = {
        "V_kisitsiz": prompts.DENEY3_SECIM_SISTEM,
        "V_kisitli": prompts.DENEY3_SECIM_SISTEM + prompts.MODUL_KISIT_AJANI,
    }
    for s in veri["senaryolar"]:
        secenek_metni = "\n".join(
            f"{k}: {v}" for k, v in s["secenekler"].items())
        user = prompts.DENEY3_SORU_SABLONU.format(
            uyusmazlik=s["uyusmazlik"], secenekler=secenek_metni)
        for konfig, system in konfigler.items():
            for t in range(tekrar):
                resp = client.complete(system, user)
                try:
                    d = parse_json_response(resp.text)
                    secim = str(d.get("secim", "")).upper().replace("İ", "I")
                except Exception:  # noqa: BLE001
                    secim = None
                yasak_secildi = (secim == s["yasak_secenek"].upper())
                yazici.yaz({
                    "deney": "deney3", "senaryo": s["id"], "konfig": konfig,
                    "tekrar": t, "secim": secim,
                    "yasak_secenek": s["yasak_secenek"],
                    "yasak_secildi": yasak_secildi,
                    "dogru_mu": (secim in [x.upper() for x in
                                           s["kabul_edilebilir"]])
                    if secim else None,
                    "model": resp.model, "provider": resp.provider,
                    "yanit": resp.text,
                })
                print(f"  [D3] {s['id']} {konfig} #{t}: seçim={secim} "
                      f"{'⚠ YASAK' if yasak_secildi else ''}")


# ===========================================================================
# Deney 4 — Kıyas yasağı maskesi
# ===========================================================================
def deney4(client: LLMClient, tekrar: int, yazici: SonucYazici):
    veri = yukle("deney4_kiyas.json")
    konfigler = {
        "V_maskesiz": prompts.TEMEL_ROL,
        "V_maskeli": prompts.TEMEL_ROL + prompts.MODUL_KIYAS_MASKESI,
    }
    for s in veri["senaryolar"]:
        user = prompts.DENEY4_SORU_SABLONU.format(
            hukum=s["hukum"], kalem=s["kalem"])
        for konfig, system in konfigler.items():
            for t in range(tekrar):
                resp = client.complete(system, user)
                karar = judge.nihai_karar_ayikla(
                    resp.text, "KAPSAMDA", "KAPSAM_DISI")
                dogru = s["dogru_cevap_etiketi"]
                yazici.yaz({
                    "deney": "deney4", "senaryo": s["id"],
                    "cift_id": s["cift_id"], "tip": s["tip"],
                    "konfig": konfig, "tekrar": t, "karar": karar,
                    "dogru_cevap": dogru,
                    "dogru_mu": (karar == dogru) if karar else None,
                    "model": resp.model, "provider": resp.provider,
                    "yanit": resp.text,
                })
                print(f"  [D4] {s['id']} {konfig} #{t}: {karar} "
                      f"({'✓' if karar == dogru else '✗'})")


# ===========================================================================
# Deney 5 — Ω skoru ve Ψ(w) nitelendirmesi
# ===========================================================================
def deney5(judge_client: LLMClient, tekrar: int, yazici: SonucYazici):
    veri = yukle("deney5_omega.json")
    agirliklar = veri["agirliklar"]
    t1, t2 = veri["esikler"]["theta1"], veri["esikler"]["theta2"]
    for s in veri["senaryolar"]:
        for t in range(tekrar):
            puanlar, gerekceler = {}, {}
            for bilesen in agirliklar:
                d = judge.omega_bilesen_puani(judge_client, bilesen, s["olay"])
                puanlar[bilesen] = d.get("puan")
                gerekceler[bilesen] = d.get("gerekce")
            f_sonuc = judge.f_yargici(judge_client, s["olay"])
            F = f_sonuc.get("F")

            if any(v is None for v in puanlar.values()) or F is None:
                omega, etiket = None, "AYRISTIRMA_HATASI"
            else:
                omega = round(sum(agirliklar[b] * puanlar[b]
                                  for b in agirliklar), 4)
                # Makale 4.9.3 Ψ(w) — DÖRT çıktı:
                # F=1 → OLGU_ALANI (Ω'dan bağımsız sevk kuralı).
                # F=0 iken yüksek Ω hiçbir zaman kaçakçılık isnadına
                # dönüşmez; Ω>θ2 yalnızca YOGUN_INCELEME yönlendirmesidir.
                if F == 1:
                    etiket = "OLGU_ALANI"
                elif omega <= t1:
                    etiket = "SERBEST_ALAN"
                elif omega <= t2:
                    etiket = "YORUM_ALANI"
                else:
                    etiket = "YOGUN_INCELEME"

            yazici.yaz({
                "deney": "deney5", "senaryo": s["id"], "tekrar": t,
                "bilesen_puanlari": puanlar, "F": F, "omega": omega,
                "etiket": etiket, "beklenen_etiket": s["beklenen_etiket"],
                "dogru_mu": etiket == s["beklenen_etiket"],
                "bilesen_gerekceleri": gerekceler,
                "f_gerekce": f_sonuc.get("gerekce"),
                "model": judge_client.model,
                "provider": judge_client.provider,
            })
            print(f"  [D5] {s['id']} #{t}: Ω={omega} F={F} → {etiket} "
                  f"(beklenen: {s['beklenen_etiket']}) "
                  f"({'✓' if etiket == s['beklenen_etiket'] else '✗'})")


# ===========================================================================
VARSAYILAN_MODELLER = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "gemini": "gemini-3.1-pro-preview",
}


def main():
    anahtarlari_yukle()

    ap = argparse.ArgumentParser(description="Makale 1 davranışsal testleri")
    ap.add_argument("--deney", default="hepsi",
                    help="1|2|3|4|5|hepsi (virgülle çoklu: 1,4)")
    ap.add_argument("--provider", default="anthropic",
                    choices=list(SAGLAYICILAR))
    ap.add_argument("--model", default=None,
                    help="Model adı (varsayılan: sağlayıcıya göre "
                         f"{VARSAYILAN_MODELLER})")
    ap.add_argument("--judge-provider", default=None,
                    choices=list(SAGLAYICILAR),
                    help="Yargıç sağlayıcısı (varsayılan: --provider)")
    ap.add_argument("--judge-model", default=None,
                    help="Yargıç modeli (varsayılan: yargıç sağlayıcısının "
                         "varsayılanı). Test edilen modelden farklı "
                         "seçilmesi önerilir.")
    ap.add_argument("--tekrar", type=int, default=5,
                    help="Senaryo başına tekrar (varsayılan 5; yayın için 10)")
    ap.add_argument("--temperature", type=float, default=0.3)
    ap.add_argument("--retriever", default="tfidf", choices=["tfidf", "st"])
    ap.add_argument("--mock", action="store_true",
                    help="API'siz boru hattı testi (sonuçlar anlamsızdır)")
    args = ap.parse_args()

    model = args.model or VARSAYILAN_MODELLER[args.provider]
    judge_provider = args.judge_provider or args.provider
    judge_model = args.judge_model or (
        model if judge_provider == args.provider
        else VARSAYILAN_MODELLER[judge_provider])

    client = LLMClient(args.provider, model,
                       temperature=args.temperature, mock=args.mock)
    judge_client = LLMClient(
        judge_provider, judge_model,
        temperature=0.0,  # yargıçta belirlenimcilik esas alınır
        mock=args.mock)

    secilen = (["1", "2", "3", "4", "5"] if args.deney == "hepsi"
               else args.deney.split(","))
    etiket = f"{args.provider}_{model.replace('/', '_')}_d{'-'.join(secilen)}"
    if args.mock:
        etiket = "MOCK_" + etiket
    yazici = SonucYazici(etiket)

    print(f"Model: {args.provider}/{model} | Yargıç: "
          f"{judge_client.provider}/{judge_client.model} | "
          f"tekrar={args.tekrar} | mock={args.mock}")
    if (judge_provider, judge_model) == (args.provider, model) and \
            ("2" in secilen or "5" in secilen):
        print("  [not] Yargıç = test edilen model. Öz-puanlama yanlılığını "
              "azaltmak için --judge-provider/--judge-model ile farklı bir "
              "model seçmeniz önerilir.")

    if "1" in secilen:
        print("\n=== Deney 1: Normlar hiyerarşisi (B^legal: H/L/M) ===")
        deney1(client, args.tekrar, yazici)
    if "2" in secilen:
        print("\n=== Deney 2: Tarihi amaçsal yorum / RAG ===")
        deney2(client, judge_client, args.tekrar, yazici, args.retriever)
    if "3" in secilen:
        print("\n=== Deney 3: Anayasal kısıt ajanı (M^const / M^leg) ===")
        deney3(client, args.tekrar, yazici)
    if "4" in secilen:
        print("\n=== Deney 4: Kıyas yasağı maskesi (K) ===")
        deney4(client, args.tekrar, yazici)
    if "5" in secilen:
        print("\n=== Deney 5: Ω öz denetim skoru ve Ψ(w) ===")
        deney5(judge_client, args.tekrar, yazici)

    yazici.kapat()
    print(f"\nSonuçlar: {yazici.yol}")
    print(f"Rapor için: python report.py {yazici.yol}")


if __name__ == "__main__":
    sys.exit(main())
