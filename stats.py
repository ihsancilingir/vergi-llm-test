"""
stats.py — Konfigürasyon karşılaştırmaları için istatistiksel testler.

Tasarım gerekçesi (makale metodolojisi ile bağ):
- Aynı senaryo-tekrar çifti iki konfigürasyonda da koşulduğu için gözlemler
  EŞLEŞTİRİLMİŞTİR; bağımsız örneklem testi (ki-kare) yerine McNemar
  kullanılır. Kesikli ve küçük örneklemlerde asimptotik ki-kare yaklaşımı
  bozulduğundan TAM (exact, binom) McNemar uygulanır.
- Oranlar için Wilson güven aralığı raporlanır (küçük n'de Wald'dan
  güvenilirdir).
Not: Aynı senaryonun tekrarları tam bağımsız gözlem değildir (küme etkisi);
raporda p değerleri bu çekince ile sunulmalı, ideal olarak senaryo sayısı
artırılmalıdır.
"""

from __future__ import annotations

import math

from scipy.stats import binomtest


def mcnemar_exact(cift_sonuclar: list[tuple[bool, bool]]) -> dict:
    """
    cift_sonuclar: her (senaryo, tekrar) çifti için
        (baseline_dogru_mu, duzeltmeli_dogru_mu)
    Tam McNemar: yalnızca uyumsuz çiftler (b: baseline doğru & düzeltmeli
    yanlış; c: baseline yanlış & düzeltmeli doğru) bilgi taşır.
    """
    b = sum(1 for x, y in cift_sonuclar if x and not y)
    c = sum(1 for x, y in cift_sonuclar if (not x) and y)
    n_uyumsuz = b + c
    if n_uyumsuz == 0:
        return {"b": b, "c": c, "p": 1.0,
                "not": "Uyumsuz çift yok; konfigürasyonlar ayrışmadı."}
    p = binomtest(min(b, c), n_uyumsuz, 0.5, alternative="two-sided").pvalue
    return {"b": b, "c": c, "n_uyumsuz": n_uyumsuz, "p": float(p)}


def wilson_araligi(basari: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Oran ve %95 Wilson güven aralığı: (oran, alt, üst)."""
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = basari / n
    merkez = (p + z * z / (2 * n)) / (1 + z * z / n)
    yarim = (z / (1 + z * z / n)) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, max(0.0, merkez - yarim), min(1.0, merkez + yarim))
