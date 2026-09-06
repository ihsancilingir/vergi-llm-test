"""
embedding_client.py -- Deney 6 (embedding katmani testi) icin vektor
temsili cikarma araclari.

API modelleri (OpenAI, Gemini) icin ozel embedding endpoint'i kullanilir.
Kumru icin API yoktur; lokal modelin son katman hidden state'lerinin
token bazinda ortalamasi (mean pooling) embedding olarak kullanilir.
Bu, llm_client.py'deki _kumru_yukle() ile ayni model onbellegini
paylasir (ayni process icinde ikinci kez indirme/yukleme olmaz).
"""

from __future__ import annotations

import numpy as np


def kosinus_benzerligi(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float64).flatten()
    b = np.asarray(b, dtype=np.float64).flatten()
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def openai_embedding(text: str, model: str = "text-embedding-3-large") -> np.ndarray:
    import openai
    client = openai.OpenAI()
    resp = client.embeddings.create(model=model, input=text)
    return np.array(resp.data[0].embedding)


def gemini_embedding(text: str, model: str = "gemini-embedding-001") -> np.ndarray:
    from google import genai
    client = genai.Client()
    resp = client.models.embed_content(model=model, contents=text)
    return np.array(resp.embeddings[0].values)


def kumru_embedding(text: str, model_adi: str = "vngrs-ai/Kumru-2B") -> np.ndarray:
    """Kumru'nun son katman hidden state'lerinin token-ortalamasi.

    llm_client._kumru_yukle ile ayni onbellegi kullanir; deney6 calisirken
    baska bir deneyde kumru zaten yuklenmisse tekrar indirme/yukleme olmaz.
    """
    import torch
    from llm_client import _kumru_yukle
    tokenizer, model = _kumru_yukle(model_adi)
    inputs = tokenizer(text, return_tensors="pt").to("cuda")
    with torch.no_grad():
        out = model(**inputs, output_hidden_states=True)
    son_katman = out.hidden_states[-1][0]  # (token_sayisi, gizli_boyut)
    ortalama = son_katman.mean(dim=0)
    return ortalama.float().cpu().numpy()


EMBEDDING_FONKSIYONLARI = {
    "openai": openai_embedding,
    "gemini": gemini_embedding,
    "kumru": kumru_embedding,
}


def embedding_al(provider: str, text: str, model: str | None = None) -> np.ndarray:
    if provider not in EMBEDDING_FONKSIYONLARI:
        raise ValueError(
            f"Embedding destegi olmayan saglayici: {provider} "
            f"(gecerli: {', '.join(EMBEDDING_FONKSIYONLARI)})")
    fn = EMBEDDING_FONKSIYONLARI[provider]
    if model:
        return fn(text, model)
    return fn(text)
