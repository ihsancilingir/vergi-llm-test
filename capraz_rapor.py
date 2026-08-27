"""
capraz_rapor.py — Birden çok JSONL sonuç dosyasını (farklı modeller)
tek bir çapraz karşılaştırma tablosuna dönüştürür.

Kullanım:
    python capraz_rapor.py results/*.jsonl [--cikti capraz_rapor.md]

Amaç (README metodolojik not 6): Makale 1'deki mimari iddialar tek modelde
doğrulanamaz. Bu rapor, "düzeltme modülü etkisi" deseninin (baseline →
düzeltmeli fark) model aileleri arasında TEKRARLANIP tekrarlanmadığını
tek bakışta gösterir. Desen üç ailede aynı yönde ise iddia model-özgü
değil, mimari düzeyde bir bulgu olarak savunulabilir.
"""

from __future__ import annotations

import argparse
import glob
import json
from collections import defaultdict

from stats import wilson_araligi


def oku(yol: str) -> list[dict]:
    with open(yol, encoding="utf-8") as f:
        return [json.loads(s) for s in f if s.strip()]


def oran(kayitlar, anahtar="dogru_mu"):
    alt = [k for k in kayitlar if k.get(anahtar) is not None]
    if not alt:
        return None
    b = sum(1 for k in alt if k[anahtar])
    p, lo, hi = wilson_araligi(b, len(alt))
    return f"{p:.0%} ({b}/{len(alt)})"


def model_adi(kayitlar) -> str:
    for k in kayitlar:
        m = str(k.get("model", "?")).replace("-mock", "")
        pr = k.get("provider", "")
        return f"{pr}/{m}" if pr else m
    return "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dosyalar", nargs="+")
    ap.add_argument("--cikti", default="capraz_rapor.md")
    args = ap.parse_args()

    # Windows CMD joker karakterleri (*.jsonl) otomatik genişletmez;
    # burada Python tarafında genişletiyoruz (Linux/Mac'te zaten
    # genişletilmiş gelir, glob.glob o durumda dosyayı olduğu gibi
    # döndürür, zararsızdır).
    dosya_listesi = []
    for desen in args.dosyalar:
        eslesen = glob.glob(desen)
        dosya_listesi.extend(eslesen if eslesen else [desen])
    if not dosya_listesi:
        print(f"Uyarı: hiçbir dosya eşleşmedi: {args.dosyalar}")
        return

    # dosya → model adı → deney → kayıtlar
    modeller: dict[str, dict[str, list]] = {}
    mock_var = False
    for yol in dosya_listesi:
        kayitlar = oku(yol)
        if not kayitlar:
            continue
        if any("mock" in str(k.get("model", "")) for k in kayitlar):
            mock_var = True
        ad = model_adi(kayitlar)
        hedef = modeller.setdefault(ad, defaultdict(list))
        for k in kayitlar:
            hedef[k["deney"]].append(k)

    adlar = sorted(modeller)
    satirlar = ["# Çapraz Model Raporu\n",
                f"Modeller: {', '.join(adlar)}\n"]
    if mock_var:
        satirlar.append("> ⚠ En az bir dosya MOCK koşusudur; ilgili "
                        "sütunlar bilimsel değer taşımaz.\n")

    def tablo(baslik, hucre_fn, aciklama=""):
        satirlar.append(f"\n## {baslik}\n")
        if aciklama:
            satirlar.append(aciklama + "\n")
        satirlar.append("| Model | " + " | ".join(
            etiket for etiket, _ in hucre_fn) + " |")
        satirlar.append("|" + "---|" * (len(hucre_fn) + 1))
        for ad in adlar:
            hucreler = []
            for _, fn in hucre_fn:
                v = fn(modeller[ad])
                hucreler.append(v if v is not None else "—")
            satirlar.append(f"| {ad} | " + " | ".join(hucreler) + " |")

    # Deney 1 --------------------------------------------------------------
    if any("deney1" in m for m in modeller.values()):
        tablo(
            "Deney 1 — Normlar hiyerarşisi (B^legal: H/L/M): doğruluk "
            "(kanun-dışı şart senaryoları)",
            [("V_baseline", lambda m: oran(
                [k for k in m.get("deney1", []) if not k.get("kontrol")
                 and k["konfig"] == "V_baseline"])),
             ("V_hiyerarsi", lambda m: oran(
                [k for k in m.get("deney1", []) if not k.get("kontrol")
                 and k["konfig"] == "V_hiyerarsi"])),
             ("Kontrol/baseline", lambda m: oran(
                [k for k in m.get("deney1", []) if k.get("kontrol")
                 and k["konfig"] == "V_baseline"])),
             ("Kontrol/hiyerarşi", lambda m: oran(
                [k for k in m.get("deney1", []) if k.get("kontrol")
                 and k["konfig"] == "V_hiyerarsi"]))],
            "Beklenen desen: ana senaryolarda V_hiyerarsi ↑, kontrolde "
            "düşüş YOK (aşırı düzeltme denetimi).")

    # Deney 2 --------------------------------------------------------------
    if any("deney2" in m for m in modeller.values()):
        tablo(
            "Deney 2 — RAG: gerekçe örtüşmesi / halüsinasyon",
            [("Örtüşme RAG'sız", lambda m: oran(
                [k for k in m.get("deney2", [])
                 if k["konfig"] == "V_ragsiz"], "ortusme")),
             ("Örtüşme RAG'lı", lambda m: oran(
                [k for k in m.get("deney2", [])
                 if k["konfig"] == "V_ragli"], "ortusme")),
             ("Halüsinasyon RAG'sız", lambda m: oran(
                [k for k in m.get("deney2", [])
                 if k["konfig"] == "V_ragsiz"], "haluinasyon")),
             ("Halüsinasyon RAG'lı", lambda m: oran(
                [k for k in m.get("deney2", [])
                 if k["konfig"] == "V_ragli"], "haluinasyon"))],
            "Beklenen desen: örtüşme ↑, halüsinasyon ↓ (RAG'lı sütunlarda).")

    # Deney 3 --------------------------------------------------------------
    if any("deney3" in m for m in modeller.values()):
        tablo(
            "Deney 3 — Anayasal kısıt (M^const/M^leg): yasak seçeneğin seçilme "
            "oranı (düşük iyi)",
            [("V_kisitsiz", lambda m: oran(
                [k for k in m.get("deney3", [])
                 if k["konfig"] == "V_kisitsiz"], "yasak_secildi")),
             ("V_kisitli", lambda m: oran(
                [k for k in m.get("deney3", [])
                 if k["konfig"] == "V_kisitli"], "yasak_secildi"))],
            "Beklenen desen: kısıtlı konfigürasyonda oran ↓ (veya her "
            "ikisinde 0 ise parametrik içselleştirme tartışılır).")

    # Deney 4 --------------------------------------------------------------
    if any("deney4" in m for m in modeller.values()):
        def kapsamda(m, konfig, tip):
            alt = [k for k in m.get("deney4", []) if k["konfig"] == konfig
                   and k["tip"] == tip and k.get("karar") is not None]
            if not alt:
                return None
            b = sum(1 for k in alt if k["karar"] == "KAPSAMDA")
            return f"{b / len(alt):.0%} ({b}/{len(alt)})"

        tablo(
            "Deney 4 — Kıyas maskesi (K): KAPSAMDA deme oranı",
            [("Tahdidî/maskesiz (hata)",
              lambda m: kapsamda(m, "V_maskesiz", "tahdidi")),
             ("Tahdidî/maskeli (hata)",
              lambda m: kapsamda(m, "V_maskeli", "tahdidi")),
             ("Tadadî/maskesiz (doğru)",
              lambda m: kapsamda(m, "V_maskesiz", "tadadi")),
             ("Tadadî/maskeli (doğru)",
              lambda m: kapsamda(m, "V_maskeli", "tadadi"))],
            "Beklenen desen: maskeli sütunda tahdidî ↓, tadadî yüksek "
            "kalır (ayrışma). İkisi birden düşerse maske aşırı "
            "kısıtlayıcıdır.")

    # Deney 5 --------------------------------------------------------------
    if any("deney5" in m for m in modeller.values()):
        def etiket_dogruluk(m):
            return oran(m.get("deney5", []))

        def f_bagimsizlik(m):
            alt = [k for k in m.get("deney5", [])
                   if k.get("F") == 1]
            if not alt:
                return None
            b = sum(1 for k in alt if k["etiket"] == "OLGU_ALANI")
            return f"{b}/{len(alt)}"

        tablo(
            "Deney 5 — Ω / Ψ(w): üçlü nitelendirme",
            [("Etiket doğruluğu", etiket_dogruluk),
             ("F=1 → OLGU_ALANI sevki", f_bagimsizlik)],
            "F sütunu: F=1 saptanan tüm koşularda etiketin Ω'dan bağımsız "
            "olarak OLGU_ALANI çıkması beklenir (bağımsız sevk kuralı).")

    with open(args.cikti, "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")
    print(f"Çapraz rapor yazıldı: {args.cikti}")


if __name__ == "__main__":
    main()
