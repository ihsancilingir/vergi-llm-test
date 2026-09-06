"""
deney6_capraz_rapor.py -- Deney 6 (embedding testi) icin coklu model
karsilastirma raporu. results/deney6_*.json dosyalarini okuyup tek
bir Markdown tabloda birlestirir.

Kullanim:
    python deney6_capraz_rapor.py
    python deney6_capraz_rapor.py --cikti results/deney6_capraz_rapor.md
"""

from __future__ import annotations

import argparse
import glob
import json
import os


def en_son_sonuclari_bul(desen: str = "results/deney6_*.json") -> dict:
    """Her saglayici icin en son (zaman damgasi en buyuk) sonuc dosyasini bulur."""
    dosyalar = glob.glob(desen)
    en_son = {}
    for yol in dosyalar:
        with open(yol, encoding="utf-8") as f:
            veri = json.load(f)
        provider = veri["provider"]
        zaman = veri["zaman"]
        if provider not in en_son or zaman > en_son[provider][0]:
            en_son[provider] = (zaman, veri)
    return {k: v[1] for k, v in en_son.items()}


def rapor_olustur(desen: str = "results/deney6_*.json") -> str:
    sonuclar = en_son_sonuclari_bul(desen)
    if not sonuclar:
        return "Hic deney6 sonuc dosyasi bulunamadi."

    satirlar = []
    satirlar.append("# Deney 6: Embedding Katmani Testi -- Coklu Model Karsilastirmasi\n")
    satirlar.append("## Kategori ortalamalari\n")
    satirlar.append("| Saglayici | kapali_lafzi | acik_lafzi | kontrol |")
    satirlar.append("|---|---|---|---|")
    for provider, veri in sorted(sonuclar.items()):
        ozet = veri["kategori_ozet"]
        kl = ozet.get("kapali_lafzi", {}).get("ortalama", 0)
        al = ozet.get("acik_lafzi", {}).get("ortalama", 0)
        kt = ozet.get("kontrol", {}).get("ortalama", 0)
        satirlar.append(f"| {provider} | {kl:.4f} | {al:.4f} | {kt:.4f} |")

    satirlar.append("\n## Istatistiksel anlamlilik (Mann-Whitney U)\n")
    satirlar.append("| Saglayici | U | p | n_lafzi | n_kontrol | Sonuc |")
    satirlar.append("|---|---|---|---|---|---|")
    for provider, veri in sorted(sonuclar.items()):
        ist = veri.get("istatistik")
        if not ist:
            satirlar.append(f"| {provider} | - | - | - | - | test yapilamadi |")
            continue
        sonuc = "anlamli" if ist["p"] < 0.05 else "anlamli degil"
        satirlar.append(
            f"| {provider} | {ist['u']:.2f} | {ist['p']:.4f} | "
            f"{ist['n_lafzi']} | {ist['n_kontrol']} | {sonuc} |")

    satirlar.append("\n## Cift bazinda karsilastirma\n")
    tum_idler = sorted({s["id"] for veri in sonuclar.values() for s in veri["sonuclar"]})
    providerlar = sorted(sonuclar.keys())
    baslik = "| ID | Terim A | Terim B | Kategori | " + " | ".join(providerlar) + " |"
    ayrac = "|---|---|---|---|" + "---|" * len(providerlar)
    satirlar.append(baslik)
    satirlar.append(ayrac)
    for cift_id in tum_idler:
        satir_verisi = {}
        terim_a = terim_b = kategori = ""
        for provider, veri in sonuclar.items():
            for s in veri["sonuclar"]:
                if s["id"] == cift_id:
                    satir_verisi[provider] = s["benzerlik"]
                    terim_a, terim_b, kategori = s["terim_a"], s["terim_b"], s["kategori"]
        degerler = " | ".join(f"{satir_verisi.get(p, '-'):.4f}"
                              if p in satir_verisi else "-" for p in providerlar)
        satirlar.append(f"| {cift_id} | {terim_a} | {terim_b} | {kategori} | {degerler} |")

    return "\n".join(satirlar)


def main():
    ap = argparse.ArgumentParser(description="Deney 6 coklu model karsilastirma raporu")
    ap.add_argument("--desen", default="results/deney6_*.json")
    ap.add_argument("--cikti", default=None,
                    help="Markdown dosyasina yaz (belirtilmezse ekrana basar)")
    args = ap.parse_args()

    rapor = rapor_olustur(args.desen)
    if args.cikti:
        with open(args.cikti, "w", encoding="utf-8") as f:
            f.write(rapor)
        print(f"Rapor yazildi: {os.path.abspath(args.cikti)}")
    else:
        print(rapor)


if __name__ == "__main__":
    main()
