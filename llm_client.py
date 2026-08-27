"""
llm_client.py — Çok sağlayıcılı LLM istemcisi (Anthropic / OpenAI / Gemini).

Makale 1 (Çilingir, kavramsal eşleştirme) davranışsal testleri için üç
model ailesine tek arayüzden erişim sağlar. README metodolojik not 6'nın
("mimari iddia tek modelde doğrulanamaz") doğrudan altyapısıdır.

Ortam değişkenleri (anahtarlar.env dosyasından da okunur, bkz. runner.py):
    ANTHROPIC_API_KEY   Anthropic modelleri için
    OPENAI_API_KEY      OpenAI modelleri için
    GEMINI_API_KEY      Google Gemini modelleri için

Mock modu (--mock): API anahtarı olmadan boru hattının uçtan uca
çalıştığını doğrulamak içindir; rastgele fakat deterministik
(seed'li) yanıtlar üretir. Bilimsel sonuç ÜRETMEZ.
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from dataclasses import dataclass

SAGLAYICILAR = ("anthropic", "openai", "gemini")


@dataclass
class LLMResponse:
    text: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0


class LLMClient:
    def __init__(self, provider: str, model: str, temperature: float = 0.3,
                 max_tokens: int = 3000, mock: bool = False, mock_seed: int = 42):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.mock = mock
        self.mock_seed = mock_seed
        self._client = None
        if not mock:
            self._init_client()

    def _init_client(self):
        if self.provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic()  # ANTHROPIC_API_KEY okur
        elif self.provider == "openai":
            import openai
            self._client = openai.OpenAI()        # OPENAI_API_KEY okur
        elif self.provider == "gemini":
            from google import genai
            self._client = genai.Client()         # GEMINI_API_KEY okur
        else:
            raise ValueError(
                f"Bilinmeyen sağlayıcı: {self.provider} "
                f"(geçerli: {', '.join(SAGLAYICILAR)})")

    # ------------------------------------------------------------------
    def complete(self, system: str, user: str, retries: int = 3) -> LLMResponse:
        """Tek turluk tamamlama. Üstel geri çekilme ile yeniden dener."""
        if self.mock:
            return self._mock_complete(system, user)

        last_err = None
        for attempt in range(retries):
            try:
                if self.provider == "anthropic":
                    return self._anthropic_complete(system, user)
                if self.provider == "openai":
                    return self._openai_complete(system, user)
                return self._gemini_complete(system, user)
            except Exception as e:  # noqa: BLE001
                last_err = e
                wait = 2 ** attempt * 2
                print(f"    [uyarı] API hatası ({e.__class__.__name__}), "
                      f"{wait}s bekleniyor... ({attempt + 1}/{retries})")
                time.sleep(wait)
        raise RuntimeError(f"API çağrısı {retries} denemede başarısız: {last_err}")

    # ------------------------------------------------------------------
    def _anthropic_complete(self, system: str, user: str) -> LLMResponse:
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        return LLMResponse(
            text=text, model=self.model, provider="anthropic",
            input_tokens=msg.usage.input_tokens,
            output_tokens=msg.usage.output_tokens,
        )

    def _openai_complete(self, system: str, user: str) -> LLMResponse:
        resp = self._client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return LLMResponse(
            text=resp.choices[0].message.content or "",
            model=self.model, provider="openai",
            input_tokens=resp.usage.prompt_tokens,
            output_tokens=resp.usage.completion_tokens,
        )

    def _gemini_complete(self, system: str, user: str) -> LLMResponse:
        from google.genai import types
        resp = self._client.models.generate_content(
            model=self.model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            ),
        )
        text = resp.text or ""
        um = getattr(resp, "usage_metadata", None)
        return LLMResponse(
            text=text, model=self.model, provider="gemini",
            input_tokens=getattr(um, "prompt_token_count", 0) or 0,
            output_tokens=getattr(um, "candidates_token_count", 0) or 0,
        )

    # ------------------------------------------------------------------
    def _mock_complete(self, system: str, user: str) -> LLMResponse:
        """Deterministik sahte yanıt üretici (boru hattı testi için)."""
        h = hashlib.sha256((system + user + str(self.mock_seed)).encode()).hexdigest()
        rng = random.Random(h)

        if "SADECE_JSON" in system:
            # Yargıç (judge) çağrısı: şemaya uygun rastgele JSON döndür.
            if "KARAR_JSON" in system:
                karar = rng.choice(["UYGULANIR", "UYGULANMAZ"])
                out = json.dumps({"karar": karar, "gerekce": "mock gerekçe"},
                                 ensure_ascii=False)
            elif "SECIM_JSON" in system:
                out = json.dumps({"secim": rng.choice(["I1", "I2", "I3"]),
                                  "gerekce": "mock gerekçe"}, ensure_ascii=False)
            elif "KAPSAM_JSON" in system:
                out = json.dumps({"karar": rng.choice(["KAPSAMDA", "KAPSAM_DISI"]),
                                  "gerekce": "mock"}, ensure_ascii=False)
            elif "OMEGA_JSON" in system:
                out = json.dumps({"puan": round(rng.uniform(0, 1), 2),
                                  "gerekce": "mock"}, ensure_ascii=False)
            elif "GEREKCE_JSON" in system:
                out = json.dumps({"amac_ifadesi": "mock amaç",
                                  "kaynak_var": rng.choice([True, False])},
                                 ensure_ascii=False)
            elif "ortusme" in system:
                # Deney 2 RAG yargıcı şeması
                out = json.dumps({"ortusme": rng.choice([True, False]),
                                  "haluinasyon": rng.choice([True, False]),
                                  "gerekce": "mock"}, ensure_ascii=False)
            else:
                out = json.dumps({"deger": rng.random()}, ensure_ascii=False)
        else:
            if "KAPSAM" in user.upper():
                out = ("MOCK gerekçe.\nNİHAİ KARAR: "
                       + rng.choice(["KAPSAMDA", "KAPSAM DIŞI"]))
            else:
                out = ("MOCK gerekçe.\nNİHAİ KARAR: "
                       + rng.choice(["ŞART UYGULANIR", "ŞART UYGULANMAZ"]))
        return LLMResponse(text=out, model=self.model + "-mock",
                           provider=self.provider)


def parse_json_response(text: str) -> dict:
    """Modelin JSON yanıtını dayanıklı biçimde ayrıştırır."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```")[1]
        if t.startswith("json"):
            t = t[4:]
    t = t.strip()
    # İlk { ile son } arasını al (giriş cümlesi kalıntılarına karşı)
    if "{" in t and "}" in t:
        t = t[t.index("{"): t.rindex("}") + 1]
    return json.loads(t)
