"""
report.py — JSONL sonuç dosyasından Markdown rapor üretir.

Kullanım:
    python report.py results/<dosya>.jsonl [rapor.md]

Rapor içeriği:
- Deney 1/4: konfigürasyon bazında doğruluk oranı + Wilson %95 GA,
  eşleştirilmiş tam McNemar testi.
- Deney 2: RAG'siz/RAG'li örtüşme ve halüsinasyon oranları + McNemar.
- Deney 3: yasak seçeneğin seçilme oranı (kısıtsız vs kısıtlı) + McNemar.
- Deney 4 ek: tahdidî/tadadî AYRIŞMA analizi (makalenin asıl ölçütü).
- Deney 5: senaryo bazında ortalama Ω, etiket doğruluğu, F kuralı denetimi.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict

from stats import mcnemar_exact, wilson_araligi


def oku(yol: str) -> list[dict]:
    with open(yol, encoding="utf-8") as f:
        return [json.loads(satir) for satir in f if satir.strip()]


def oran_str(basari: int, n: int) -> str:
    p, alt, ust = wilson_araligi(basari, n)
    if n == 0:
        return "n=0"
    return f"{p:.2%} ({basari}/{n}; %95 GA [{alt:.2%}, {ust:.2%}])"


def eslesmis_ciftler(kayitlar, konfig_a, konfig_b, anahtar="dogru_mu"):
    """(senaryo, tekrar) anahtarıyla iki konfigürasyonu eşleştirir."""
    a = {(k["senaryo"], k["tekrar"]): k[anahtar] for k in kayitlar
         if k["konfig"] == konfig_a and k[anahtar] is not None}
    b = {(k["senaryo"], k["tekrar"]): k[anahtar] for k in kayitlar
         if k["konfig"] == konfig_b and k[anahtar] is not None}
    ortak = sorted(set(a) & set(b))
    return [(bool(a[k]), bool(b[k])) for k in ortak]


def bolum_konfig_karsilastirma(satirlar, kayitlar, baslik, konfig_a, konfig_b,
                               anahtar="dogru_mu", olcut_adi="doğruluk"):
    satirlar.append(f"\n## {baslik}\n")
    for konfig in (konfig_a, konfig_b):
        alt = [k for k in kayitlar if k["konfig"] == konfig
               and k[anahtar] is not None]
        basari = sum(1 for k in alt if k[anahtar])
        satirlar.append(f"- **{konfig}** {olcut_adi}: "
                        f"{oran_str(basari, len(alt))}")
    ciftler = eslesmis_ciftler(kayitlar, konfig_a, konfig_b, anahtar)
    mc = mcnemar_exact(ciftler)
    satirlar.append(f"- Eşleştirilmiş tam McNemar: b={mc['b']}, c={mc['c']}, "
                    f"p={mc['p']:.4f}"
                    + (f" — {mc['not']}" if "not" in mc else ""))
    satirlar.append("")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    yol = sys.argv[1]
    cikti = sys.argv[2] if len(sys.argv) > 2 else yol.replace(".jsonl", "_rapor.md")
    kayitlar = oku(yol)
    gruplar = defaultdict(list)
    for k in kayitlar:
        gruplar[k["deney"]].append(k)

    satirlar = [f"# Deney Raporu\n\nKaynak: `{yol}`  \n"
                f"Toplam kayıt: {len(kayitlar)}\n"]
    if any("mock" in str(k.get("model", "")) for k in kayitlar):
        satirlar.append("> ⚠ **MOCK KOŞUSU** — sonuçlar yalnızca boru hattı "
                        "doğrulamasıdır, bilimsel değer taşımaz.\n")

    # --- Deney 1 ---------------------------------------------------------
    if "deney1" in gruplar:
        d = gruplar["deney1"]
        ana = [k for k in d if not k.get("kontrol")]
        kontrol = [k for k in d if k.get("kontrol")]
        bolum_konfig_karsilastirma(
            satirlar, ana,
            "Deney 1 — Normlar hiyerarşisi düzeltmesi (B^legal: H/L/M) "
            "[kanun-dışı şart senaryoları]",
            "V_baseline", "V_hiyerarsi")
        if kontrol:
            satirlar.append("### Kontrol senaryosu (kanuni dayanaklı şart — "
                            "aşırı düzeltme denetimi)\n")
            for konfig in ("V_baseline", "V_hiyerarsi"):
                alt = [k for k in kontrol if k["konfig"] == konfig
                       and k["dogru_mu"] is not None]
                basari = sum(1 for k in alt if k["dogru_mu"])
                satirlar.append(f"- **{konfig}**: {oran_str(basari, len(alt))}")
            satirlar.append(
                "\nYorum notu: Hiyerarşi modülü kontrol senaryosunda doğruluğu "
                "DÜŞÜRÜYORSA model aşırı düzeltme yapıyor demektir (her tebliğ "
                "şartını reddetme); makaledeki γ·H teriminin 'açıklayıcı "
                "tebliğ hükümlerini koruma' iddiası zayıflar.\n")

    # --- Deney 2 ---------------------------------------------------------
    if "deney2" in gruplar:
        d = gruplar["deney2"]
        bolum_konfig_karsilastirma(
            satirlar, d, "Deney 2 — Tarihi amaçsal yorum / RAG: "
            "gerekçeyle örtüşme", "V_ragsiz", "V_ragli",
            anahtar="ortusme", olcut_adi="örtüşme")
        # Halüsinasyon (düşük olması iyi)
        satirlar.append("### Halüsinasyon (uydurma amaç atfı) oranı — "
                        "düşük olması istenir\n")
        for konfig in ("V_ragsiz", "V_ragli"):
            alt = [k for k in d if k["konfig"] == konfig
                   and k["haluinasyon"] is not None]
            h = sum(1 for k in alt if k["haluinasyon"])
            satirlar.append(f"- **{konfig}**: {oran_str(h, len(alt))}")
        tuzak = [k for k in d if k.get("tuzak")]
        if tuzak:
            satirlar.append("\n### Yürürlük-tarihi tuzağı (4.5.2 tarihsel "
                            "düzeltme)\n")
            for konfig in ("V_ragsiz", "V_ragli"):
                alt = [k for k in tuzak if k["konfig"] == konfig
                       and k["ortusme"] is not None]
                b = sum(1 for k in alt if k["ortusme"])
                satirlar.append(f"- **{konfig}** örtüşme: "
                                f"{oran_str(b, len(alt))}")
            satirlar.append("")

    # --- Deney 3 ---------------------------------------------------------
    if "deney3" in gruplar:
        d = gruplar["deney3"]
        satirlar.append("\n## Deney 3 — Anayasal kısıt ajanı (M^leg): "
                        "yasak seçeneğin seçilme oranı — düşük olması "
                        "istenir\n")
        for konfig in ("V_kisitsiz", "V_kisitli"):
            alt = [k for k in d if k["konfig"] == konfig
                   and k["secim"] is not None]
            y = sum(1 for k in alt if k["yasak_secildi"])
            satirlar.append(f"- **{konfig}**: {oran_str(y, len(alt))}")
        ciftler = eslesmis_ciftler(d, "V_kisitsiz", "V_kisitli",
                                   anahtar="yasak_secildi")
        mc = mcnemar_exact(ciftler)
        satirlar.append(f"- Eşleştirilmiş tam McNemar: b={mc['b']}, "
                        f"c={mc['c']}, p={mc['p']:.4f}"
                        + (f" — {mc['not']}" if "not" in mc else ""))
        satirlar.append(
            "\nYorum notu: Kısıtsız koşulda yasak seçenek hiç seçilmiyorsa "
            "iki olasılık vardır: (a) model kısıtı parametrik olarak "
            "içselleştirmiştir, (b) senaryolar yeterince 'cazip' değildir. "
            "(b)'yi elemek için yasak seçeneğin amaçsal çekiciliğini artıran "
            "yeni senaryolar eklenmelidir.\n")

    # --- Deney 4 ---------------------------------------------------------
    if "deney4" in gruplar:
        d = gruplar["deney4"]
        bolum_konfig_karsilastirma(
            satirlar, d, "Deney 4 — Kıyas yasağı maskesi (K, 4.8.1): "
            "genel doğruluk", "V_maskesiz", "V_maskeli")
        satirlar.append("### Ayrışma analizi (makalenin asıl ölçütü)\n")
        satirlar.append("Analojik aşırı genelleme = tahdidî hükümde KAPSAMDA "
                        "deme oranı (hata). Meşru genişletme = tadadî hükümde "
                        "KAPSAMDA deme oranı (doğru).\n")
        for konfig in ("V_maskesiz", "V_maskeli"):
            for tip, ad in (("tahdidi", "analojik aşırı genelleme (hata)"),
                            ("tadadi", "meşru genişletme (doğru)")):
                alt = [k for k in d if k["konfig"] == konfig
                       and k["tip"] == tip and k["karar"] is not None]
                kap = sum(1 for k in alt if k["karar"] == "KAPSAMDA")
                satirlar.append(f"- **{konfig} / {tip}** — {ad}: "
                                f"{oran_str(kap, len(alt))}")
        satirlar.append(
            "\nYorum notu: İdeal desen, maskeli konfigürasyonda tahdidî "
            "oranın düşüp tadadî oranın yüksek kalmasıdır. İkisi birden "
            "düşüyorsa maske aşırı kısıtlayıcıdır (meşru yorumu da "
            "engelliyor); makaledeki 'varsayılan yasak, istisnaî izin' "
            "modelinin izin kolu çalışmıyor demektir.\n")

    # --- Deney 5 ---------------------------------------------------------
    if "deney5" in gruplar:
        d = gruplar["deney5"]
        satirlar.append("\n## Deney 5 — Ω öz denetim skoru ve Ψ(w) "
                        "nitelendirmesi\n")
        seny = defaultdict(list)
        for k in d:
            seny[k["senaryo"]].append(k)
        satirlar.append("| Senaryo | Ort. Ω | F=1 oranı | Etiket doğruluğu | "
                        "Beklenen |")
        satirlar.append("|---|---|---|---|---|")
        for sid, alt in sorted(seny.items()):
            gecerli = [k for k in alt if k["omega"] is not None]
            ort = (sum(k["omega"] for k in gecerli) / len(gecerli)
                   if gecerli else float("nan"))
            f1 = sum(1 for k in alt if k.get("F") == 1)
            dog = sum(1 for k in alt if k["dogru_mu"])
            satirlar.append(
                f"| {sid} | {ort:.3f} | {f1}/{len(alt)} | "
                f"{dog}/{len(alt)} | {alt[0]['beklenen_etiket']} |")
        satirlar.append(
            "\nEtiketler (makale 4.9.3): SERBEST_ALAN (F=0, Ω≤θ₁), YORUM_ALANI "
            "(F=0, θ₁<Ω≤θ₂), YOGUN_INCELEME (F=0, Ω>θ₂), OLGU_ALANI (F=1).\n"
            "\nYorum notu: (1) F=1 senaryosunda etiketin Ω değerinden "
            "bağımsız olarak OLGU_ALANI çıkması, makaledeki bağımsız sevk "
            "kuralının doğrulamasıdır. (2) Tekrarlar arası Ω varyansı "
            "yüksekse LLM-as-judge puanlaması kararsızdır; bileşen "
            "tanımlarının netleştirilmesi veya few-shot çapa örnekleri "
            "eklenmesi gerekir. (3) Eşikler (θ₁, θ₂) bu veriyle "
            "kalibre edilmemiştir; senaryo sayısı artırıldıktan sonra "
            "ROC benzeri bir tarama ile ayarlanmalıdır.\n")

    with open(cikti, "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar))
    print(f"Rapor yazıldı: {cikti}")


if __name__ == "__main__":
    main()
