"""
Country Financial Insights Agent.

This module orchestrates calls to the currency, stock, and maps tools to
produce a structured view of a country's financial market information.

It also exposes an optional LLM-powered summary using LangChain with
configurable model backends (Gemini, Llama 3, Mistral, DeepSeek).
"""

from __future__ import annotations

import os
from typing import Dict, Any, Literal

from dotenv import load_dotenv

from tools.currency_tool import (
    get_currency_for_country,
    get_exchange_rates_for_currency,
)
from tools.stock_tool import get_country_stock_profile
from tools.maps_tool import get_google_maps_link_for_address

from langchain_core.messages import SystemMessage, HumanMessage

try:
    # Gemini / Google GenAI
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:  # pragma: no cover - optional dependency
    ChatGoogleGenerativeAI = None  # type: ignore

try:
    # Generic OpenAI-compatible chat models (for Llama 3, Mistral, DeepSeek)
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - optional dependency
    ChatOpenAI = None  # type: ignore


load_dotenv()

LLMProvider = Literal["gemini", "llama3", "mistral", "deepseek"]


def build_country_financial_profile(country: str) -> Dict[str, Any]:
    """
    High-level orchestrator that calls the various tools and returns a single dict.

    The returned structure is safe to render directly in the Streamlit app.
    """
    country = country.strip()

    # 1. Currency information
    currency_info = get_currency_for_country(country)

    # 2. Exchange rates (only if we have a currency code)
    if "currency_code" in currency_info:
        fx_rates = get_exchange_rates_for_currency(currency_info["currency_code"])
    else:
        fx_rates = {
            "error": "Could not determine currency code for this country; FX rates unavailable.",
        }

    # 3. Stock exchanges and index values
    stock_profile = get_country_stock_profile(country)

    # 4. Maps link for HQ of the main stock exchange (first configured exchange)
    maps_link = None
    main_hq_address = None
    exchanges = stock_profile.get("exchanges") or []
    if exchanges:
        main_exchange = exchanges[0]
        main_hq_address = main_exchange.get("headquarters_address")
        if main_hq_address:
            maps_link = get_google_maps_link_for_address(main_hq_address)

    return {
        "country": country,
        "currency": currency_info,
        "exchange_rates": fx_rates,
        "stocks": stock_profile,
        "main_exchange_hq_address": main_hq_address,
        "google_maps_link": maps_link,
    }


def _get_llm(provider: LLMProvider | None = None):
    """
    Construct an LLM client using LangChain based on environment configuration.

    Supported providers:
      - gemini  (GOOGLE_API_KEY, model via GEMINI_MODEL_NAME or default)
      - llama3  (OpenAI-compatible, e.g. Groq; GROQ_API_KEY and GROQ_BASE_URL)
      - mistral (Mistral AI; MISTRAL_API_KEY)
      - deepseek (DeepSeek; DEEPSEEK_API_KEY)
    """
    provider = provider or os.getenv("LLM_PROVIDER", "gemini").lower()  # type: ignore[assignment]

    if provider == "gemini":
        if ChatGoogleGenerativeAI is None:
            raise RuntimeError("langchain-google-genai is not installed.")
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set; cannot use Gemini.")
        model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")
        return ChatGoogleGenerativeAI(
            model=model_name,
            api_key=api_key,
            temperature=0.2,
            convert_system_message_to_human=True,
        )

    if ChatOpenAI is None:
        raise RuntimeError(
            "langchain-openai is not installed. Install it or use provider=gemini."
        )

    if provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is not set; cannot use DeepSeek.")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        model_name = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=0.2,
        )

    if provider == "llama3":
        # Example configuration for Groq-hosted Llama 3.
        api_key = os.getenv("GROQ_API_KEY")
        base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set; cannot use Llama 3.")
        model_name = os.getenv("LLAMA3_MODEL_NAME", "llama-3.1-70b-versatile")
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=0.2,
        )

    if provider == "mistral":
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY is not set; cannot use Mistral.")
        base_url = os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1")
        model_name = os.getenv("MISTRAL_MODEL_NAME", "mistral-large-latest")
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=0.2,
        )

    raise ValueError(f"Unsupported LLM provider: {provider}")


def generate_llm_summary(profile: Dict[str, Any], provider: LLMProvider | None = None) -> str:
    """
    Use the configured LLM to generate a short natural-language summary describing:
      - The country's official currency
      - How that currency trades vs USD/INR/GBP/EUR
      - The key stock exchanges and indices
    """
    llm = _get_llm(provider)

    country = profile.get("country", "")
    currency = profile.get("currency", {})
    fx = profile.get("exchange_rates", {})
    stocks = profile.get("stocks", {})

    prompt = (
        "You are a financial markets assistant. Given the structured JSON data below, "
        "write a concise (2–3 paragraphs) explanation of this country's currency and "
        "stock market landscape. Include:\n"
        "- The official currency (name + code)\n"
        "- How 1 unit of that currency compares to USD, INR, GBP, and EUR (relative strength)\n"
        "- The major stock exchanges and indices and what they broadly represent\n\n"
        "Avoid repeating raw numbers exhaustively; instead, interpret them qualitatively.\n\n"
        f"Country: {country}\n"
        f"Currency JSON: {currency}\n"
        f"Exchange rates JSON: {fx}\n"
        f"Stock profile JSON: {stocks}\n"
    )

    messages = [
        SystemMessage(content="You are a concise, accurate financial markets explainer."),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    # LangChain chat models return an object with a .content string
    return getattr(response, "content", str(response))


__all__ = [
    "build_country_financial_profile",
    "generate_llm_summary",
]

