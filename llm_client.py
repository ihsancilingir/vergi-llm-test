"""
llm_client.py -- Cok saglayicili LLM istemcisi
(Anthropic / OpenAI / Gemini / DeepSeek / Mistral / Grok).

DeepSeek, Mistral ve Grok, OpenAI SDK ile uyumlu chat.completions
endpoint'i sundugu icin tek bir _openai_uyumlu_complete metodu
uzerinden calisirlar (base_url farkli, istek/yanit semasi ayni).

Ortam degiskenleri (anahtarlar.env):
    ANTHROPIC_API_KEY   Anthropic modelleri icin
    OPENAI_API_KEY      OpenAI modelleri icin
    GEMINI_API_KEY      Google Gemini modelleri icin
    DEEPSEEK_API_KEY    DeepSeek modelleri icin
    MISTRAL_API_KEY     Mistral modelleri icin
    XAI_API_KEY         Grok (xAI) modelleri icin

Mock modu (--mock): API anahtari olmadan boru hattinin uctan uca
calistigini dogrulamak icindir; rastgele fakat deterministik
(seed'li) yanitlar uretir. Bilimsel sonuc URETMEZ.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import time
from dataclasses import dataclass

SAGLAYICILAR = ("anthropic", "openai", "gemini", "deepseek", "grok", "kumru")

# OpenAI SDK uyumlu (base_url farkli) saglayicilar
_OPENAI_UYUMLU_BASE_URL = {
    "deepseek": "https://api.deepseek.com",
    "grok": "https://api.x.ai/v1",
}

_OPENAI_UYUMLU_ENV_KEY = {
    "deepseek": "DEEPSEEK_API_KEY",
    "grok": "XAI_API_KEY",
}


@dataclass
class LLMResponse:
    text: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0


# Kumru gibi lokal HF modelleri process icinde bir kez yuklenir, tekrar
# tekrar yuklenmez (GPU bellegi ve zaman tasarrufu icin).
_LOKAL_MODEL_ONBELLEK: dict = {}


def _kumru_yukle(model_adi: str):
    if model_adi in _LOKAL_MODEL_ONBELLEK:
        return _LOKAL_MODEL_ONBELLEK[model_adi]
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch as _torch
    tokenizer = AutoTokenizer.from_pretrained(model_adi)
    model = AutoModelForCausalLM.from_pretrained(
        model_adi, dtype=_torch.bfloat16, device_map="cuda")
    _LOKAL_MODEL_ONBELLEK[model_adi] = (tokenizer, model)
    return tokenizer, model


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
        elif self.provider in _OPENAI_UYUMLU_BASE_URL:
            import openai
            env_key = _OPENAI_UYUMLU_ENV_KEY[self.provider]
            api_key = os.environ.get(env_key)
            if not api_key:
                raise RuntimeError(
                    f"{env_key} tanimli degil (anahtarlar.env dosyasina ekleyin)")
            self._client = openai.OpenAI(
                api_key=api_key,
                base_url=_OPENAI_UYUMLU_BASE_URL[self.provider],
            )
        elif self.provider == "kumru":
            # Lokal HF modeli: API anahtari gerekmez, GPU'ya yuklenir.
            self._tokenizer, self._client = _kumru_yukle(self.model)
        else:
            raise ValueError(
                f"Bilinmeyen saglayici: {self.provider} "
                f"(gecerli: {', '.join(SAGLAYICILAR)})")

    # ------------------------------------------------------------------
    def complete(self, system: str, user: str, retries: int = 3) -> LLMResponse:
        """Tek turluk tamamlama. Ustel geri cekilme ile yeniden dener."""
        if self.mock:
            return self._mock_complete(system, user)

        last_err = None
        for attempt in range(retries):
            try:
                if self.provider == "anthropic":
                    return self._anthropic_complete(system, user)
                if self.provider == "gemini":
                    return self._gemini_complete(system, user)
                if self.provider == "kumru":
                    return self._kumru_complete(system, user)
                return self._openai_uyumlu_complete(system, user)
            except Exception as e:  # noqa: BLE001
                last_err = e
                wait = 2 ** attempt * 2
                print(f"    [uyari] API hatasi ({e.__class__.__name__}), "
                      f"{wait}s bekleniyor... ({attempt + 1}/{retries})")
                time.sleep(wait)
        raise RuntimeError(f"API cagrisi {retries} denemede basarisiz: {last_err}")

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

    def _openai_uyumlu_complete(self, system: str, user: str) -> LLMResponse:
        """openai, deepseek, mistral, grok icin ortak yol."""
        resp = self._client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        usage = getattr(resp, "usage", None)
        return LLMResponse(
            text=resp.choices[0].message.content or "",
            model=self.model, provider=self.provider,
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
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

    def _kumru_complete(self, system: str, user: str) -> LLMResponse:
        """Lokal Kumru modeli ile uretim (API cagrisi degil)."""
        import torch
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        inputs = self._tokenizer.apply_chat_template(
            messages, add_generation_prompt=True,
            return_dict=True, return_tensors="pt").to("cuda")
        with torch.no_grad():
            out = self._client.generate(
                **inputs, max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                do_sample=self.temperature > 0,
            )
        girdi_uzunlugu = inputs["input_ids"].shape[1]
        text = self._tokenizer.decode(
            out[0][girdi_uzunlugu:], skip_special_tokens=True)
        return LLMResponse(
            text=text, model=self.model, provider="kumru",
            input_tokens=girdi_uzunlugu,
            output_tokens=out.shape[1] - girdi_uzunlugu,
        )

    # ------------------------------------------------------------------
    def _mock_complete(self, system: str, user: str) -> LLMResponse:
        """Deterministik sahte yanit uretici (boru hatti testi icin)."""
        h = hashlib.sha256((system + user + str(self.mock_seed)).encode()).hexdigest()
        rng = random.Random(h)

        if "SADECE_JSON" in system:
            if "KARAR_JSON" in system:
                karar = rng.choice(["UYGULANIR", "UYGULANMAZ"])
                out = json.dumps({"karar": karar, "gerekce": "mock gerekce"},
                                 ensure_ascii=False)
            elif "SECIM_JSON" in system:
                out = json.dumps({"secim": rng.choice(["I1", "I2", "I3"]),
                                  "gerekce": "mock gerekce"}, ensure_ascii=False)
            elif "KAPSAM_JSON" in system:
                out = json.dumps({"karar": rng.choice(["KAPSAMDA", "KAPSAM_DISI"]),
                                  "gerekce": "mock"}, ensure_ascii=False)
            elif "OMEGA_JSON" in system:
                out = json.dumps({"puan": round(rng.uniform(0, 1), 2),
                                  "gerekce": "mock"}, ensure_ascii=False)
            elif "GEREKCE_JSON" in system:
                out = json.dumps({"amac_ifadesi": "mock amac",
                                  "kaynak_var": rng.choice([True, False])},
                                 ensure_ascii=False)
            elif "ortusme" in system:
                out = json.dumps({"ortusme": rng.choice([True, False]),
                                  "haluinasyon": rng.choice([True, False]),
                                  "gerekce": "mock"}, ensure_ascii=False)
            else:
                out = json.dumps({"deger": rng.random()}, ensure_ascii=False)
        else:
            if "KAPSAM" in user.upper():
                out = ("MOCK gerekce.\nNIHAI KARAR: "
                       + rng.choice(["KAPSAMDA", "KAPSAM DISI"]))
            else:
                out = ("MOCK gerekce.\nNIHAI KARAR: "
                       + rng.choice(["SART UYGULANIR", "SART UYGULANMAZ"]))
        return LLMResponse(text=out, model=self.model + "-mock",
                           provider=self.provider)


def parse_json_response(text: str) -> dict:
    """Modelin JSON yanitini dayanikli bicimde ayristirir."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```")[1]
        if t.startswith("json"):
            t = t[4:]
    t = t.strip()
    if "{" in t and "}" in t:
        t = t[t.index("{"): t.rindex("}") + 1]
    return json.loads(t)
