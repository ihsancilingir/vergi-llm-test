"""
deney6_calistir.py -- Embedding katmani testi (Deney 6) calistiricisi.

Kullanim:
    python deney6_calistir.py --provider openai
    python deney6_calistir.py --provider kumru
    python deney6_calistir.py --provider openai,gemini,kumru   # coklu, tek raporda

Her cift icin cumle_a / cumle_b temsilleri cikarilir, kosinus benzerligi
hesaplanir. Kategori bazinda ortalama benzerlik raporlanir; kapali_lafzi
ve acik_lafzi kategorilerinde DUSUK, kontrol kategorisinde YUKSEK benzerlik
beklenir (bkz. scenarios/deney6_embedding.json).
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime

def anahtarlari_yukle():
    """anahtarlar.env varsa KEY=VALUE satirlarini ortama yukler.

    Mevcut ortam degiskenlerini ezmez; # ile baslayan satirlari atlar.
    (runner.py ile ayni mantik, python-dotenv bagimliligi eklemekten kacinmak icin.)
    """
    dosya = "anahtarlar.env"
    if not os.path.exists(dosya):
        return
    with open(dosya, encoding="utf-8") as f:
        for satir in f:
            satir = satir.strip()
            if not satir or satir.startswith("#") or "=" not in satir:
                continue
            ad, deger = satir.split("=", 1)
            ad, deger = ad.strip(), deger.strip().strip(chr(34)).strip(chr(39))
            if ad and deger and ad not in os.environ:
                os.environ[ad] = deger


def _centroid(provider: str, cumleler: list) -> "np.ndarray":
    import numpy as np
    from embedding_client import embedding_al
    vektorler = [embedding_al(provider, c) for c in cumleler]
    return np.mean(np.stack(vektorler), axis=0)


def _mannwhitney_testi(kategori_toplamlari: dict) -> dict | None:
    """Lafzi kategoriler (kapali+acik) ile kontrol kategorisi arasindaki
    farkin anlamliligini test eder. Kucuk orneklem oldugu icin parametrik
    olmayan Mann-Whitney U kullanilir."""
    try:
        from scipy.stats import mannwhitneyu
    except ImportError:
        return None
    lafzi = (kategori_toplamlari.get("kapali_lafzi", [])
             + kategori_toplamlari.get("acik_lafzi", []))
    kontrol = kategori_toplamlari.get("kontrol", [])
    if not lafzi or not kontrol:
        return None
    u, p = mannwhitneyu(kontrol, lafzi, alternative="greater")
    return {"u": float(u), "p": float(p), "n_lafzi": len(lafzi), "n_kontrol": len(kontrol)}


def calistir(provider: str, senaryo_yolu: str = "scenarios/deney6_embedding.json"):
    from embedding_client import kosinus_benzerligi

    with open(senaryo_yolu, encoding="utf-8") as f:
        veri = json.load(f)

    sonuclar = []
    kategori_toplamlari = defaultdict(list)

    print(f"\n=== Deney 6: Embedding katmani testi -- saglayici={provider} ===")
    for cift in veri["ciftler"]:
        try:
            emb_a = _centroid(provider, cift["cumleler_a"])
            emb_b = _centroid(provider, cift["cumleler_b"])
            benzerlik = kosinus_benzerligi(emb_a, emb_b)
        except Exception as e:  # noqa: BLE001
            print(f"  [HATA] {cift['id']}: {e.__class__.__name__}: {e}")
            continue

        kategori = cift["kategori"]
        kategori_toplamlari[kategori].append(benzerlik)
        sonuclar.append({
            "id": cift["id"], "kategori": kategori,
            "terim_a": cift["terim_a"], "terim_b": cift["terim_b"],
            "benzerlik": round(benzerlik, 4),
            "beklenen_iliski": cift["beklenen_iliski"],
        })
        print(f"  [{cift['id']}] {cift['terim_a']:<22} vs {cift['terim_b']:<18} "
              f"benzerlik={benzerlik:.4f}  (beklenen: {cift['beklenen_iliski']})")

    print("\n--- Kategori ozeti ---")
    for kategori, degerler in kategori_toplamlari.items():
        ortalama = sum(degerler) / len(degerler)
        print(f"  {kategori:<15} n={len(degerler):<3} ortalama_benzerlik={ortalama:.4f}")

    istatistik = _mannwhitney_testi(kategori_toplamlari)
    if istatistik:
        print("\n--- Istatistiksel anlamlilik (Mann-Whitney U) ---")
        n_l = istatistik["n_lafzi"]
        n_k = istatistik["n_kontrol"]
        u_deger = istatistik["u"]
        p_deger = istatistik["p"]
        anlamli = "anlamli (p<0.05)" if p_deger < 0.05 else "anlamli degil"
        print(f"  lafzi (kapali+acik, n={n_l}) vs kontrol (n={n_k})")
        print(f"  U={u_deger:.2f}  p={p_deger:.4f}  ({anlamli})")

    os.makedirs("results", exist_ok=True)
    zaman = datetime.now().strftime("%Y%m%d_%H%M%S")
    cikti_yolu = f"results/deney6_{provider}_{zaman}.json"
    with open(cikti_yolu, "w", encoding="utf-8") as f:
        json.dump({
            "provider": provider,
            "zaman": zaman,
            "sonuclar": sonuclar,
            "kategori_ozet": {
                k: {"n": len(v), "ortalama": sum(v) / len(v)}
                for k, v in kategori_toplamlari.items()
            },
            "istatistik": istatistik,
        }, f, ensure_ascii=False, indent=2)
    print(f"\nSonuclar: {os.path.abspath(cikti_yolu)}")
    return cikti_yolu


def main():
    anahtarlari_yukle()
    ap = argparse.ArgumentParser(description="Deney 6: Embedding katmani testi")
    ap.add_argument("--provider", required=True,
                    help="openai|gemini|kumru (virgulle coklu: openai,gemini,kumru)")
    ap.add_argument("--senaryo", default="scenarios/deney6_embedding.json")
    args = ap.parse_args()

    saglayicilar = [p.strip() for p in args.provider.split(",")]
    for provider in saglayicilar:
        calistir(provider, args.senaryo)


if __name__ == "__main__":
    main()
