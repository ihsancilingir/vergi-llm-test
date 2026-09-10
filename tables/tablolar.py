#!/usr/bin/env python3
"""
tablolar.py — Makale 2 (Ampirik) tablolarını results/ klasöründeki ham
kayıtlardan yeniden üretir.

Girdi : results/*_d1-2-3-4-5_*.jsonl  (altı model; Deney 1-5, test modeli koşuları)
        results/*_d5_*.jsonl           (Deney 5 ikinci yargıç koşusu)
        results/deney6_*.json          (üç temsil mimarisi)
Çıktı : tables/tablolar.md  (bütün tablolar, markdown)
        tables/*.csv        (tablo başına bir CSV)
        results/capraz_rapor_tam.md (--capraz ile)
        stdout              (çapraz rapor sayımlarıyla doğrulama)

İstatistik:
  - Wilson %95 güven aralığı (Wilson 1927)
  - Kesin McNemar, üç düzeyde:
      (a) marjinal sınır: b ve c yalnızca koşul toplamlarından; p_min-p_max
      (b) birim eşleştirme: aynı (senaryo, tekrar) indeksi iki koşulda eşlenir;
          bir koşulda eksik olan birim eşleştirmeden düşer; b, c kesin
      (c) senaryo düzeyi: her senaryonun iki koşuldaki doğru sayısı; kesin işaret testi
  - Mann-Whitney U, kesin, tek yönlü (Deney 6)

Kullanım: python tables/tablolar.py --results results --out tables --capraz
"""
import argparse, glob, json, os, csv, statistics
from math import sqrt
from collections import defaultdict, Counter
from scipy.stats import binomtest, mannwhitneyu

MODEL_AD = {"anthropic": "Claude Sonnet 4.6", "openai": "GPT-4o", "gemini": "Gemini 3.6 Flash",
            "deepseek": "DeepSeek v4-flash", "grok": "Grok 4.6", "kumru": "Kumru-2B"}
SIRA = ["anthropic", "openai", "gemini", "deepseek", "grok", "kumru"]

# ---------- istatistik yardımcıları ----------
def wilson(x, n, z=1.959964):
    if n == 0: return (float("nan"), float("nan"))
    p = x / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * (c - h), 100 * (c + h))

def mcnemar_exact(b, c):
    if b + c == 0: return float("nan")
    return binomtest(min(b, c), b + c, 0.5).pvalue

def mcnemar_marginal(x1, n1, x2, n2):
    """b, c ve p için marjinallerden türeyen sınırlar (eşleştirme yapısı bilinmediğinde)."""
    n = min(n1, n2); x1 = min(x1, n); x2 = min(x2, n); d = x2 - x1
    bmin = max(0, -d); bmax = min(x1, n - x2)
    return bmin, bmax, bmin + d, bmax + d, mcnemar_exact(bmin, bmin + d), mcnemar_exact(bmax, bmax + d)

def mcnemar_paired(units1, units2):
    """units: {(senaryo,tekrar): bool}. Ortak birimler üzerinden kesin b, c."""
    ortak = [k for k in units1 if k in units2 and units1[k] is not None and units2[k] is not None]
    b = sum(1 for k in ortak if units1[k] and not units2[k])
    c = sum(1 for k in ortak if not units1[k] and units2[k])
    return len(ortak), b, c, mcnemar_exact(b, c)

def isaret_testi_senaryo(units1, units2):
    """Senaryo düzeyi: her senaryonun iki koşuldaki doğru oranı; kesin işaret testi."""
    s1, s2 = defaultdict(list), defaultdict(list)
    for (s, t), v in units1.items():
        if v is not None: s1[s].append(v)
    for (s, t), v in units2.items():
        if v is not None: s2[s].append(v)
    art = dus = 0
    for s in s1:
        if s not in s2: continue
        p1 = sum(s1[s]) / len(s1[s]); p2 = sum(s2[s]) / len(s2[s])
        if p2 > p1: art += 1
        elif p2 < p1: dus += 1
    return art, dus, mcnemar_exact(dus, art)

def fmt_p(p):
    if p != p: return "—"
    if p >= 0.001: return f"{p:.3f}".replace(".", ",")
    m, e = f"{p:.1e}".split("e"); return f"{m.replace('.', ',')} × 10^{int(e)}"

def fmt_oran(x, n):
    lo, hi = wilson(x, n)
    return f"%{100*x/n:.0f} ({x}/{n}) [%{lo:.0f}–%{hi:.0f}]"

def sonuc_etiketi(pmin, pmax, yon):
    if pmin != pmin: return "Çift tavan / sıfır varyans"
    if pmax < 0.05: return f"Anlamlı ({yon})" if yon else "Anlamlı"
    if pmin >= 0.05: return "Anlamlı değil"
    return "Eşleşmeye bağlı"

# ---------- ham kayıtları yükle ----------
def yukle(results):
    kayit = defaultdict(list)          # provider -> records (test koşuları)
    d5_ek = []                          # ikinci yargıç koşusu
    for f in sorted(glob.glob(os.path.join(results, "*.jsonl"))):
        rs = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
        if "_d5_" in os.path.basename(f) and all(r["deney"] == "deney5" for r in rs):
            d5_ek.extend(rs); continue
        kayit[rs[0]["provider"]].extend(rs)
    d6 = {}
    for f in sorted(glob.glob(os.path.join(results, "deney6_*.json"))):
        j = json.load(open(f, encoding="utf-8")); d6[j["provider"]] = j
    return kayit, d5_ek, d6

def birimler(rs, deney, konfig, alan, filtre=lambda r: True):
    """(senaryo,tekrar) -> değer (None = eksik ölçüm)"""
    return {(r["senaryo"], r["tekrar"]): r[alan]
            for r in rs if r["deney"] == deney and r["konfig"] == konfig and filtre(r)}

def sayim(u):
    v = [x for x in u.values() if x is not None]
    return sum(1 for x in v if x), len(v), sum(1 for x in u.values() if x is None)

# ---------- tablo üreticiler ----------
def cift_tablo(kayit, deney, k1, k2, alan, filtre, bloklar, baslik):
    """Genel iki-koşul tablosu. bloklar: [(blok_adı, filtre)]"""
    satirlar = []
    for blok_ad, bf in bloklar:
        satirlar.append([f"*{blok_ad}*"] + [""] * 8)
        for p in SIRA:
            rs = kayit[p]
            u1 = birimler(rs, deney, k1, alan, lambda r: filtre(r) and bf(r))
            u2 = birimler(rs, deney, k2, alan, lambda r: filtre(r) and bf(r))
            x1, n1, e1 = sayim(u1); x2, n2, e2 = sayim(u2)
            bmin, bmax, cmin, cmax, pmin, pmax = mcnemar_marginal(x1, n1, x2, n2)
            no, b, c, pb = mcnemar_paired(u1, u2)
            art, dus, ps = isaret_testi_senaryo(u1, u2)
            yon = ""
            if x2 / max(n2, 1) > x1 / max(n1, 1): yon = "artış"
            elif x2 / max(n2, 1) < x1 / max(n1, 1): yon = "düşüş"
            bc_marj = f"{bmin} / {cmin}" if bmin == bmax else f"{bmin}–{bmax} / {cmin}–{cmax}"
            p_marj = fmt_p(pmin) if pmin == pmax or (pmin != pmin) else f"{fmt_p(pmin)} – {fmt_p(pmax)}"
            satirlar.append([MODEL_AD[p], fmt_oran(x1, n1), fmt_oran(x2, n2), bc_marj, p_marj,
                             f"{b} / {c} (n={no})", fmt_p(pb), f"{art}↑ {dus}↓, p={fmt_p(ps)}",
                             sonuc_etiketi(pmin, pmax, yon)])
    kolon = ["Model", k1, k2, "b / c (marjinal)", "p (marjinal min–max)", "b / c (birim eşleşme)",
             "p (birim)", "Senaryo düzeyi", "Sonuç"]
    return baslik, kolon, satirlar

def tablo_deney1(kayit):
    return cift_tablo(kayit, "deney1", "V_baseline", "V_hiyerarsi", "dogru_mu", lambda r: True,
                      [("Ana senaryolar", lambda r: not r["kontrol"]), ("Kontrol senaryoları", lambda r: r["kontrol"])],
                      "Tablo 2. Deney 1 — normlar hiyerarşisi müdahalesi (doğru cevap oranı)")

def tablo_deney2(kayit):
    b1, k, s1 = cift_tablo(kayit, "deney2", "V_ragsiz", "V_ragli", "ortusme", lambda r: True,
                           [("Gerekçe örtüşmesi", lambda r: True)], "")
    for p in SIRA:                      # halüsinasyon: 'doğru' = halüsinasyon yok
        for r in kayit[p]:
            if r["deney"] == "deney2": r["_halusyok"] = None if r["haluinasyon"] is None else (not r["haluinasyon"])
    b2, k, s2 = cift_tablo(kayit, "deney2", "V_ragsiz", "V_ragli", "_halusyok", lambda r: True,
                           [("Halüsinasyonsuz ölçüm oranı (c > b = halüsinasyon azaldı)", lambda r: True)], "")
    return "Tablo 3. Deney 2 — gerekçe temelli bilgi erişimi", k, s1 + s2

def tablo_deney3(kayit):
    satirlar = []; kolon = ["Model", "Koşul", "n", "I₂ (yasak)", "I₁", "I₃", "Belirsiz (birden çok)", "Çözümlenemeyen", "Wilson üst sınır (I₂ / çözümlenen)"]
    top = Counter()
    for p in SIRA:
        for konf in ("V_kisitsiz", "V_kisitli"):
            rs = [r for r in kayit[p] if r["deney"] == "deney3" and r["konfig"] == konf]
            n = len(rs); yasak = sum(1 for r in rs if r["yasak_secildi"])
            i1 = sum(1 for r in rs if r["secim"] == "I1"); i3 = sum(1 for r in rs if r["secim"] == "I3")
            bel = sum(1 for r in rs if r["secim"] and "|" in r["secim"]); coz = sum(1 for r in rs if r["secim"] is None)
            cozumlenen = n - coz
            ub = wilson(yasak, cozumlenen)[1] if cozumlenen else float("nan")
            satirlar.append([MODEL_AD[p], konf, n, yasak, i1, i3, bel, coz, f"%{ub:.1f} (n={cozumlenen})".replace(".", ",")])
            top[konf] += cozumlenen; top[konf + "_y"] += yasak
    for konf in ("V_kisitsiz", "V_kisitli"):
        satirlar.append(["Birleşik (çözümlenen)", konf, top[konf], top[konf + "_y"], "", "", "", "",
                         f"%{wilson(top[konf+'_y'], top[konf])[1]:.2f}".replace(".", ",")])
    return "Tablo 4. Deney 3 — anayasal kısıt maskesi (seçim dağılımı)", kolon, satirlar

def tablo_deney4(kayit):
    return cift_tablo(kayit, "deney4", "V_maskesiz", "V_maskeli", "dogru_mu", lambda r: True,
                      [("Tahdidî hükümler (doğru = kapsam dışı)", lambda r: r["tip"] == "tahdidi"),
                       ("Tadadî hükümler (doğru = kapsamda)", lambda r: r["tip"] == "tadadi")],
                      "Tablo 5. Deney 4 — izin kuralı temelli kıyas maskesi (doğru cevap oranı)")

def tablo_deney5(kayit, d5_ek):
    kosular = {"Claude Sonnet 4.6 (yargıç)": [r for r in kayit["anthropic"] if r["deney"] == "deney5"],
               f"{d5_ek[0]['model']} (yargıç)": d5_ek}
    kolon = ["Ölçüt"] + list(kosular.keys()); satirlar = []
    def row(ad, f): satirlar.append([ad] + [f(v) for v in kosular.values()])
    row("F = 1 → olgu alanı", lambda v: (lambda F: fmt_oran(sum(1 for r in F if r["etiket"] == "OLGU_ALANI"), len(F)))([r for r in v if r["F"] == 1]))
    row("Uzman etiketiyle uyum", lambda v: fmt_oran(sum(1 for r in v if r["dogru_mu"]), len(v)))
    row("Ortalama Ω", lambda v: f"{statistics.mean(r['omega'] for r in v):.3f}".replace(".", ","))
    row("Senaryo içi Ω std. sapması (ort.)", lambda v: f"{statistics.mean(statistics.pstdev([r['omega'] for r in v if r['senaryo']==s]) for s in {r['senaryo'] for r in v}):.3f}".replace(".", ","))
    row("Uyumsuzluk dağılımı", lambda v: "; ".join(f"{a}→{b}: {n}" for (a, b), n in Counter((r["beklenen_etiket"], r["etiket"]) for r in v if not r["dogru_mu"]).items()))
    row("Serbest→olgu / olgu→serbest", lambda v: str(sum(1 for r in v if {r['beklenen_etiket'], r['etiket']} == {"SERBEST_ALAN", "OLGU_ALANI"})))
    return "Tablo 6. Deney 5 — Ω/Ψ çerçevesinin iki değerlendiricide tutarlılığı", kolon, satirlar

def tablo_deney6(d6):
    kolon = ["Model", "Kapalı lâfzî", "Açık lâfzî", "Kontrol", "U", "p", "Lâfzî maks / kontrol min"]; satirlar = []
    for p, j in d6.items():
        s = j["sonuclar"]
        laf = [x["benzerlik"] for x in s if x["kategori"] != "kontrol"]; kon = [x["benzerlik"] for x in s if x["kategori"] == "kontrol"]
        u, pv = mannwhitneyu(kon, laf, alternative="greater", method="exact")
        ort = lambda k: statistics.mean(x["benzerlik"] for x in s if x["kategori"] == k)
        satirlar.append([p, f"{ort('kapali_lafzi'):.2f}", f"{ort('acik_lafzi'):.2f}", f"{ort('kontrol'):.2f}", f"{u:.1f}", fmt_p(pv), f"{max(laf):.2f} / {min(kon):.2f}"])
    return "Tablo 7. Deney 6 — temsil düzeyi (ortalama kosinüs; Mann-Whitney U, tek yönlü)", kolon, satirlar

# ---------- çapraz rapor doğrulaması ----------
def dogrula(kayit):
    print("Çapraz rapor sayımlarının ham kayıtlardan yeniden üretimi:")
    for p in SIRA:
        rs = kayit[p]
        d1 = {k: sayim(birimler(rs, "deney1", k, "dogru_mu", lambda r: not r["kontrol"])) for k in ("V_baseline", "V_hiyerarsi")}
        d1k = {k: sayim(birimler(rs, "deney1", k, "dogru_mu", lambda r: r["kontrol"])) for k in ("V_baseline", "V_hiyerarsi")}
        d2 = {k: sayim(birimler(rs, "deney2", k, "ortusme")) for k in ("V_ragsiz", "V_ragli")}
        d2h = {k: sayim(birimler(rs, "deney2", k, "haluinasyon")) for k in ("V_ragsiz", "V_ragli")}
        d3 = {k: sum(1 for r in rs if r["deney"] == "deney3" and r["konfig"] == k and r["yasak_secildi"]) for k in ("V_kisitsiz", "V_kisitli")}
        d4 = {(k, t): sayim(birimler(rs, "deney4", k, "dogru_mu", lambda r, t=t: r["tip"] == t)) for k in ("V_maskesiz", "V_maskeli") for t in ("tahdidi", "tadadi")}
        print(f"  {MODEL_AD[p]:18s} D1 {d1} kontrol {d1k}\n{'':21s}D2 örtüşme {d2} halüs {d2h}\n{'':21s}D3 yasak {d3}\n{'':21s}D4 {d4}")

# ---------- çıktı ----------
def md_tablo(baslik, kolon, satirlar):
    out = [f"**{baslik}**", "", "| " + " | ".join(kolon) + " |", "|" + "---|" * len(kolon)]
    out += ["| " + " | ".join(str(x) for x in s) + " |" for s in satirlar]
    return "\n".join(out) + "\n"

# ---------- çapraz model raporu (düzeltilmiş biçim) ----------
def _o(x, n, eksik=0):
    s = f"{100*x/n:.0f}% ({x}/{n})" if n else "—"
    return s + (f" [{eksik} çözümlenemeyen]" if eksik else "")

def capraz_rapor(kayit, d5_ek, d6, yol):
    L = ["# Çapraz Model Raporu (ham kayıtlardan yeniden üretilmiş sürüm)", "",
         "Bu rapor `tables/tablolar.py` tarafından `results/` klasöründeki ham kayıtlardan üretilir. "
         "Oranların paydası çözümlenebilen ölçüm sayısıdır; modelin çözümlenebilir bir karar üretmediği ölçümler "
         "(`karar`/`secim` = None) köşeli parantez içinde ayrıca gösterilir ve hiçbir orana dâhil edilmez.", "",
         "Modeller: " + ", ".join(f"{p}/{kayit[p][0]['model']}" for p in SIRA), ""]
    L += ["## Deney 1 — Normlar hiyerarşisi (B^legal): kanun-dışı şart senaryolarında doğruluk", "",
          "Beklenen desen: ana senaryolarda V_hiyerarsi ↑; kontrol senaryolarında (kanuni dayanağı olan şart) düşüş YOK (aşırı düzeltme denetimi).", "",
          "| Model | V_baseline | V_hiyerarsi | Kontrol/baseline | Kontrol/hiyerarşi |", "|---|---|---|---|---|"]
    for p in SIRA:
        rs = kayit[p]; c = []
        for kon, k in ((False, "V_baseline"), (False, "V_hiyerarsi"), (True, "V_baseline"), (True, "V_hiyerarsi")):
            x, n, e = sayim(birimler(rs, "deney1", k, "dogru_mu", lambda r, kon=kon: r["kontrol"] == kon)); c.append(_o(x, n, e))
        L.append(f"| {MODEL_AD[p]} | " + " | ".join(c) + " |")
    L += ["", "## Deney 2 — RAG: gerekçe örtüşmesi / halüsinasyon (yargıç modelce puanlanmıştır)", "",
          "Beklenen desen: örtüşme ↑, halüsinasyon ↓ (RAG'lı sütunlarda). Halüsinasyon = gerekçede bulunmayan bir amacın uydurulması.", "",
          "| Model | Örtüşme RAG'sız | Örtüşme RAG'lı | Halüsinasyon RAG'sız | Halüsinasyon RAG'lı |", "|---|---|---|---|---|"]
    for p in SIRA:
        rs = kayit[p]; c = []
        for alan in ("ortusme", "haluinasyon"):
            for k in ("V_ragsiz", "V_ragli"):
                x, n, e = sayim(birimler(rs, "deney2", k, alan)); c.append(_o(x, n, e))
        L.append(f"| {MODEL_AD[p]} | " + " | ".join(c) + " |")
    L += ["", "## Deney 3 — Anayasal kısıt (M^const): üç seçenek arasında seçim dağılımı", "",
          "I₂ kanunilik ilkesini ihlal eden yasak seçenektir; I₁ ve I₃ kabul edilebilir seçeneklerdir. "
          "\"Belirsiz\" = birden çok seçenek işaretlendi; \"çözümlenemeyen\" = cevaptan seçim çıkarılamadı. "
          "Yasak seçim oranının paydası çözümlenen ölçüm sayısıdır; çözümlenen sayısı düşük olan satırlar (özellikle Kumru-2B) yorumlanamaz.", "",
          "| Model | Koşul | I₂ yasak / çözümlenen | I₁ | I₃ | Belirsiz | Çözümlenemeyen |", "|---|---|---|---|---|---|---|"]
    for p in SIRA:
        for k in ("V_kisitsiz", "V_kisitli"):
            rs = [r for r in kayit[p] if r["deney"] == "deney3" and r["konfig"] == k]
            y = sum(1 for r in rs if r["yasak_secildi"]); i1 = sum(1 for r in rs if r["secim"] == "I1"); i3 = sum(1 for r in rs if r["secim"] == "I3")
            bel = sum(1 for r in rs if r["secim"] and "|" in r["secim"]); coz = sum(1 for r in rs if r["secim"] is None)
            L.append(f"| {MODEL_AD[p]} | {k} | {_o(y, len(rs)-coz)} | {i1} | {i3} | {bel} | {coz} |")
    L += ["", "## Deney 4 — Kıyas maskesi (K): tahdidî hükümde KAPSAMDA deme (hata) / tadadî hükümde KAPSAMDA deme (doğru)", "",
          "Beklenen desen: maskeli sütunda tahdidî hata ↓, tadadî doğruluk yüksek kalır (ayrışma). İkisi birden düşerse maske aşırı kısıtlayıcıdır.", "",
          "| Model | Tahdidî/maskesiz (hata) | Tahdidî/maskeli (hata) | Tadadî/maskesiz (doğru) | Tadadî/maskeli (doğru) |", "|---|---|---|---|---|"]
    for p in SIRA:
        rs = kayit[p]; c = []
        for tip in ("tahdidi", "tadadi"):
            for k in ("V_maskesiz", "V_maskeli"):
                u = birimler(rs, "deney4", k, "dogru_mu", lambda r, tip=tip: r["tip"] == tip); x, n, e = sayim(u)
                c.append(_o(n - x if tip == "tahdidi" else x, n, e))
        L.append(f"| {MODEL_AD[p]} | " + " | ".join(c) + " |")
    L += ["", "## Deney 5 — Ω / Ψ(w): dört çıktılı nitelendirme (yalnızca yargıç model çalışır)", "",
          "Bu deneyde test modeli çağrılmaz; bileşen puanları, F ve Ω tamamen yargıç model tarafından üretilir. "
          "Aşağıdaki satırlar bu nedenle yargıç bazında verilmiştir. Yargıç sıcaklık 0 ile koşulmuş, tekrarlar neredeyse özdeş çıkmıştır (Ω senaryo içi std. sapması sütunda).", "",
          "| Yargıç | Etiket doğruluğu | F=1 → OLGU_ALANI | Ortalama Ω | Senaryo içi Ω sd | Uyumsuzluk dağılımı |", "|---|---|---|---|---|---|"]
    kosular = [("claude-sonnet-4-6", [r for r in kayit["anthropic"] if r["deney"] == "deney5"]), (d5_ek[0]["model"], d5_ek)]
    for ad, v in kosular:
        F = [r for r in v if r["F"] == 1]
        sd = statistics.mean(statistics.pstdev([r["omega"] for r in v if r["senaryo"] == s]) for s in {r["senaryo"] for r in v})
        uy = "; ".join(f"{a}→{b}: {n}" for (a, b), n in Counter((r["beklenen_etiket"], r["etiket"]) for r in v if not r["dogru_mu"]).items())
        L.append(f"| {ad} | {_o(sum(1 for r in v if r['dogru_mu']), len(v))} | {sum(1 for r in F if r['etiket']=='OLGU_ALANI')}/{len(F)} | {statistics.mean(r['omega'] for r in v):.3f} | {sd:.3f} | {uy} |")
    L += ["", "Not: Altı sağlayıcı dosyasındaki Deney 5 kayıtlarının tamamı aynı yargıçla (claude-sonnet-4-6) üretildiğinden birbirinin tekrarıdır (110/150, 30/30, Ω ≈ 0,62); "
          "ikinci yargıç koşusu ayrı dosyadadır (`*_d5_*.jsonl`)."]
    L += ["", "## Deney 6 — Temsil düzeyi: kanuni-teknik terim çiftleri ile kontrol çiftlerinin kosinüs benzerliği", "",
          "| Sağlayıcı | Kapalı lâfzî (n=8) | Açık lâfzî (n=6) | Kontrol (n=6) | U | p (tek yönlü, kesin) | Lâfzî maks / kontrol min |", "|---|---|---|---|---|---|---|"]
    for p, j in d6.items():
        s = j["sonuclar"]; laf = [x["benzerlik"] for x in s if x["kategori"] != "kontrol"]; kon = [x["benzerlik"] for x in s if x["kategori"] == "kontrol"]
        u, pv = mannwhitneyu(kon, laf, alternative="greater", method="exact")
        ort = lambda k: statistics.mean(x["benzerlik"] for x in s if x["kategori"] == k)
        L.append(f"| {p} | {ort('kapali_lafzi'):.3f} | {ort('acik_lafzi'):.3f} | {ort('kontrol'):.3f} | {u:.1f} | {pv:.4g} | {max(laf):.3f} / {min(kon):.3f} |")
    open(yol, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("Yazıldı:", yol)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results"); ap.add_argument("--out", default="tables")
    ap.add_argument("--capraz", action="store_true", help="results/capraz_rapor_tam.md dosyasını da üret")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    kayit, d5_ek, d6 = yukle(a.results)
    dogrula(kayit)
    tablolar = [tablo_deney1(kayit), tablo_deney2(kayit), tablo_deney3(kayit), tablo_deney4(kayit), tablo_deney5(kayit, d5_ek), tablo_deney6(d6)]
    md = ["# Makale 2 tabloları (tablolar.py ile results/ klasöründen üretilmiştir)\n"]
    for i, (b, k, s) in enumerate(tablolar, 2):
        md.append(md_tablo(b, k, s))
        with open(os.path.join(a.out, f"tablo{i}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(k); w.writerows(s)
    open(os.path.join(a.out, "tablolar.md"), "w", encoding="utf-8").write("\n".join(md))
    print(f"\nYazıldı: {a.out}/tablolar.md ve tablo2–7.csv")
    if a.capraz: capraz_rapor(kayit, d5_ek, d6, os.path.join(a.results, "capraz_rapor_tam.md"))

if __name__ == "__main__":
    main()