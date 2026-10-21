import hashlib
import json
import logging
import os
import re
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar
import urllib.request
import urllib.error

from pydantic import BaseModel, ValidationError
from lessongen.config import settings

logger = logging.getLogger("lessongen.llm")

T = TypeVar("T", bound=BaseModel)

class Provider(str, Enum):
    GEMINI = "gemini"
    GROQ = "groq"
    OLLAMA = "ollama"
    MOCK = "mock"

class LLMClient:
    """Provider-agnostic LLM caller with caching, rate-limit backoff, and Pydantic validation."""

    _gemini_quota_exhausted: bool = True

    def __init__(self, mock: bool = False):
        self.mock = mock
        self._last_call_time = 0.0
        if settings.CACHE_ENABLED:
            settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, cache_key: str) -> Path:
        return settings.CACHE_DIR / f"{cache_key}.json"

    def _compute_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _read_cache(self, key: str) -> Optional[str]:
        if not settings.CACHE_ENABLED or self.mock:
            return None
        cache_file = self._get_cache_path(key)
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("response")
            except Exception as e:
                logger.warning(f"Error reading cache {cache_file}: {e}")
        return None

    def _write_cache(self, key: str, prompt: str, response: str, model: str) -> None:
        if not settings.CACHE_ENABLED or self.mock:
            return
        cache_file = self._get_cache_path(key)
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": time.time(),
                    "model": model,
                    "prompt": prompt,
                    "response": response
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Error writing cache {cache_file}: {e}")

    def _throttle(self) -> None:
        """Enforces a small delay between consecutive live calls to protect free-tier rate limits."""
        if self.mock:
            return
        elapsed = time.time() - self._last_call_time
        if elapsed < settings.RATE_LIMIT_DELAY_SECONDS:
            time.sleep(settings.RATE_LIMIT_DELAY_SECONDS - elapsed)
        self._last_call_time = time.time()

    def generate(
        self,
        prompt: str,
        provider: Provider = Provider.GEMINI,
        model: Optional[str] = None,
        temperature: float = 0.7,
        system_instruction: Optional[str] = None,
        mock_response: Optional[str] = None
    ) -> str:
        """Generates raw text response with caching and exponential backoff retry."""
        if self.mock or provider == Provider.MOCK:
            if mock_response is not None:
                return mock_response
            return self._mock_generator_fallback(prompt)

        # If Gemini daily quota is known to be exhausted, bypass directly to Groq
        if provider == Provider.GEMINI and LLMClient._gemini_quota_exhausted and settings.GROQ_API_KEY:
            logger.info("Gemini quota previously exhausted; routing directly to Groq (qwen/qwen3.8-27b).")
            provider = Provider.GROQ
            model = model or "qwen/qwen3.8-27b"

        model_name = model or (settings.GEN_MODEL if provider == Provider.GEMINI else settings.JUDGE_MODEL)
        full_key_str = f"{provider}:{model_name}:{temperature}:{system_instruction or ''}:{prompt}"
        cache_key = self._compute_hash(full_key_str)

        cached = self._read_cache(cache_key)
        if cached is not None:
            logger.info(f"LLM cache hit for {provider}:{model_name}")
            return cached

        self._throttle()

        max_retries = 3
        delay = 1.0
        last_exception = None

        for attempt in range(max_retries):
            try:
                if provider == Provider.GEMINI:
                    result = self._call_gemini(prompt, model_name, temperature, system_instruction)
                elif provider == Provider.GROQ:
                    result = self._call_groq(prompt, model_name, temperature, system_instruction)
                elif provider == Provider.OLLAMA:
                    result = self._call_ollama(prompt, model_name, temperature, system_instruction)
                else:
                    raise ValueError(f"Unsupported provider: {provider}")

                self._write_cache(cache_key, prompt, result, model_name)
                return result

            except Exception as e:
                last_exception = e
                err_str = str(e).lower()
                is_rate_limit = any(x in err_str for x in [
                    "429", "rate limit", "quota", "resource_exhausted",
                    "503", "unavailable", "high demand", "overloaded"
                ])

                # Immediate resilient fallback: If Gemini hits 429 quota exhaustion (e.g. 20 req/day limit) or 503,
                # immediately route via Groq free tier so user pipeline never halts!
                if provider == Provider.GEMINI and is_rate_limit and settings.GROQ_API_KEY:
                    LLMClient._gemini_quota_exhausted = True
                    logger.warning(f"Gemini API rate limit/quota issue ({e}). Auto-falling back to Groq (qwen/qwen3.8-27b)...")
                    try:
                        result = self._call_groq(prompt, "qwen/qwen3.8-27b", temperature, system_instruction)
                        self._write_cache(cache_key, prompt, result, "qwen/qwen3.8-27b")
                        return result
                    except Exception as fb_err:
                        logger.error(f"Fallback to Groq failed: {fb_err}")

                if is_rate_limit and attempt < max_retries - 1:
                    sleep_time = delay * (2 ** attempt)
                    logger.warning(f"Temporary rate limit/spike on {provider} ({e}). Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed {provider} call after {max_retries} attempts: {e}")
                        raise e
                    time.sleep(delay)

        raise last_exception or RuntimeError("Unknown error in generate")

    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        provider: Provider = Provider.GROQ,
        model: Optional[str] = None,
        temperature: float = 0.0,
        mock_response: Optional[str] = None
    ) -> T:
        """Generates structured output validated against a Pydantic model with 1x auto-repair on JSON error."""
        json_prompt = (
            f"{prompt}\n\n"
            f"IMPORTANT: You must output ONLY a valid JSON object matching this schema:\n"
            f"{json.dumps(response_model.model_json_schema(), indent=2)}\n"
            f"Do not include any text before or after the JSON. Output raw JSON or standard markdown code fence."
        )

        raw_output = self.generate(
            prompt=json_prompt,
            provider=provider,
            model=model,
            temperature=temperature,
            mock_response=mock_response
        )

        parsed, error_msg = self._try_parse_json(raw_output, response_model)
        if parsed is not None:
            return parsed

        # Auto-retry once on malformed JSON
        logger.warning(f"JSON validation failed: {error_msg}. Attempting 1x schema repair...")
        repair_prompt = (
            f"Your previous response could not be parsed into the required schema:\n"
            f"Error: {error_msg}\n\n"
            f"Previous output was:\n{raw_output}\n\n"
            f"Please output the corrected JSON conforming strictly to:\n"
            f"{json.dumps(response_model.model_json_schema(), indent=2)}"
        )
        repaired_raw = self.generate(
            prompt=repair_prompt,
            provider=provider,
            model=model,
            temperature=0.0
        )
        repaired, repair_err = self._try_parse_json(repaired_raw, response_model)
        if repaired is not None:
            return repaired

        raise ValueError(f"Failed to generate valid structured data for {response_model.__name__}: {repair_err}\nRaw text was:\n{repaired_raw}")

    def _try_parse_json(self, text: str, model_cls: Type[T]) -> tuple[Optional[T], Optional[str]]:
        cleaned = text.strip()
        # Remove markdown code fences if present
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned)
            cleaned = re.sub(r"```$", "", cleaned)
            cleaned = cleaned.strip()

        # Extract innermost JSON if extra text surrounds it
        json_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if json_match:
            candidate = json_match.group(1)
        else:
            candidate = cleaned

        try:
            instance = model_cls.model_validate_json(candidate)
            return instance, None
        except ValidationError as ve:
            return None, str(ve)
        except Exception as ex:
            return None, str(ex)

    def _call_gemini(self, prompt: str, model_name: str, temperature: float, system_instruction: Optional[str]) -> str:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in environment or .env")
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction
        )
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )
        if not response.text:
            raise ValueError("Empty response received from Gemini API")
        return response.text

    def _call_groq(self, prompt: str, model_name: str, temperature: float, system_instruction: Optional[str]) -> str:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in environment or .env")
        from groq import Groq

        client = Groq(api_key=settings.GROQ_API_KEY)
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        max_tok = 750 if "qwen" in model_name.lower() else 2048
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tok
        )
        msg = response.choices[0].message
        content = msg.content
        if not content and hasattr(msg, "reasoning") and msg.reasoning:
            content = msg.reasoning
        if not content:
            raise ValueError("Empty response received from Groq API")
        return content

    def _call_ollama(self, prompt: str, model_name: str, temperature: float, system_instruction: Optional[str]) -> str:
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": model_name or settings.OLLAMA_MODEL,
            "prompt": prompt,
            "system": system_instruction or "",
            "stream": False,
            "options": {"temperature": temperature}
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
                return resp_json.get("response", "")
        except urllib.error.URLError as e:
            raise ConnectionError(f"Could not reach Ollama at {url}: {e}")

    def _mock_generator_fallback(self, prompt: str) -> str:
        """Generic fallback when mock response is not pre-populated."""
        return "Mock response for query."
