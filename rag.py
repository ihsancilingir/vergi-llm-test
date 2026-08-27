"""
rag.py — Deney 2 için basit bilgi erişim katmanı.

Küçük gerekçe korpusları için ağır altyapı (vektör veritabanı) gerekmez.
Varsayılan getirici TF-IDF'tir (sklearn, tamamen yerel). İsteğe bağlı
olarak sentence-transformers ile çok dilli yoğun (dense) embedding
kullanılabilir; bu, makalenin embedding tezine daha sadık bir kurulumdur
ancak model indirme gerektirir:

    pip install sentence-transformers
    python runner.py --deney 2 --retriever st ...
"""

from __future__ import annotations

import numpy as np


class Retriever:
    def __init__(self, korpus: list[dict], yontem: str = "tfidf"):
        """korpus: [{belge_id, baslik, metin}, ...]"""
        self.korpus = korpus
        self.yontem = yontem
        self._metinler = [d["baslik"] + "\n" + d["metin"] for d in korpus]

        if yontem == "tfidf":
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
            self._matris = self._vec.fit_transform(self._metinler)
        elif yontem == "st":
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                "paraphrase-multilingual-MiniLM-L12-v2")
            emb = self._model.encode(self._metinler, normalize_embeddings=True)
            self._matris = np.asarray(emb)
        else:
            raise ValueError(f"Bilinmeyen getirici: {yontem}")

    def getir(self, sorgu: str, k: int = 2) -> list[dict]:
        """Sorguya en yakın k belgeyi kosinüs benzerliğine göre döndürür."""
        if self.yontem == "tfidf":
            q = self._vec.transform([sorgu])
            skorlar = (self._matris @ q.T).toarray().ravel()
        else:
            q = self._model.encode([sorgu], normalize_embeddings=True)
            skorlar = (self._matris @ np.asarray(q).T).ravel()

        sirali = np.argsort(-skorlar)[:k]
        return [
            {**self.korpus[i], "benzerlik": float(skorlar[i])}
            for i in sirali
        ]


def kaynaklari_bicimlendir(belgeler: list[dict]) -> str:
    parcalar = []
    for d in belgeler:
        parcalar.append(f"[{d['belge_id']}] {d['baslik']}\n{d['metin']}")
    return "\n\n".join(parcalar)
