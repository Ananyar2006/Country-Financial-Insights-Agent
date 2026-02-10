"""
Country Financial Insights Agent - Streamlit App

Run:
    streamlit run app.py
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import streamlit as st
from dotenv import load_dotenv

from agent import build_country_financial_profile, generate_llm_summary


load_dotenv()


# ----- Streamlit page configuration and styling -----

st.set_page_config(
    page_title="Country Financial Insights Agent",
    page_icon="💹",
    layout="wide",
)

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    .stApp {
        background: radial-gradient(circle at top left, #0f172a 0, #020617 45%, #020617 100%);
        color: #e2e8f0;
        font-family: 'DM Sans', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'DM Sans', sans-serif !important;
    }
    .app-title {
        font-size: 2.3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .app-subtitle {
        color: #94a3b8;
        font-size: 0.98rem;
        margin-bottom: 1.8rem;
    }
    .chip-button > button {
        border-radius: 999px !important;
        border: 1px solid rgba(148, 163, 184, 0.6) !important;
        background: rgba(15, 23, 42, 0.9) !important;
        color: #e2e8f0 !important;
        padding: 0.25rem 0.9rem !important;
        font-size: 0.86rem !important;
    }
    .chip-button > button:hover {
        border-color: #38bdf8 !important;
        background: rgba(56, 189, 248, 0.12) !important;
    }
    .section-card {
        background: rgba(15, 23, 42, 0.94);
        border-radius: 14px;
        border: 1px solid rgba(51, 65, 85, 0.9);
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #e5e7eb;
        margin-bottom: 0.4rem;
    }
    .muted {
        color: #9ca3af;
        font-size: 0.85rem;
    }
    .metric-label {
        color: #9ca3af;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.05rem;
    }
    .metric-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: #e5e7eb;
    }
    .exchange-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid rgba(148, 163, 184, 0.4);
        font-size: 0.78rem;
        color: #e5e7eb;
        margin-right: 0.3rem;
        margin-bottom: 0.3rem;
    }
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617 0%, #020617 40%, #020617 100%);
    }
</style>
""",
    unsafe_allow_html=True,
)


EXAMPLE_COUNTRIES = ["Japan", "India", "United States", "United Kingdom", "South Korea", "China"]


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown("#### Configuration")
        
        st.markdown("**LLM Provider**")
        current_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        provider = st.selectbox(
            "Choose backend model",
            options=["gemini", "llama3", "mistral", "deepseek"],
            index=["gemini", "llama3", "mistral", "deepseek"].index(current_provider)
            if current_provider in ["gemini", "llama3", "mistral", "deepseek"]
            else 0,
            help="This controls which LLM is used for the natural-language summary.",
        )
        st.session_state["llm_provider"] = provider


def _render_header() -> None:
    st.markdown('<p class="app-title">💹 Country Financial Insights Agent</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="app-subtitle">Enter a country and get its official currency, live FX rates, '
        "major stock exchanges and indices, plus a Google Maps link to the main exchange HQ.</p>",
        unsafe_allow_html=True,
    )


def _render_country_input() -> str:
    col1, col2 = st.columns([2.5, 3])
    with col1:
        country = st.text_input(
            "Country name",
            value=st.session_state.get("country_input", "India"),
            placeholder="e.g. India, Japan, United States",
        )
        st.session_state["country_input"] = country
    with col2:
        st.write("Examples")
        chips_cols = st.columns(len(EXAMPLE_COUNTRIES))
        for label, col in zip(EXAMPLE_COUNTRIES, chips_cols):
            with col:
                if st.container().button(label, key=f"chip-{label}", use_container_width=True):
                    st.session_state["country_input"] = label
                    st.rerun()
    return st.session_state["country_input"]


def _render_exchange_rate_table(rates: Dict[str, float], base: str) -> None:
    if not rates:
        st.info("No exchange-rate data available.")
        return
    rows: List[Dict[str, Any]] = []
    for code, value in rates.items():
        if value is None:
            continue
        rows.append(
            {
                "From": f"1 {base}",
                "To": code,
                "Rate": f"{value:,.4f}",
            }
        )
    if not rows:
        st.info("No exchange-rate data available.")
        return
    st.table(rows)


def _render_stock_section(profile: Dict[str, Any]) -> None:
    exchanges = profile.get("exchanges") or []
    if not exchanges:
        error = profile.get("error")
        if error:
            st.warning(error)
        else:
            st.info("No stock exchange data available for this country.")
        return

    for ex in exchanges:
        st.markdown(
            f"<div class='section-card'>"
            f"<div class='section-title'>{ex.get('name')}</div>"
            f"<p class='muted'>{ex.get('city')}, {ex.get('country')}</p>",
            unsafe_allow_html=True,
        )

        indices = ex.get("indices") or []
        if indices:
            rows = []
            for idx in indices:
                price = idx.get("last_price")
                rows.append(
                    {
                        "Index": idx.get("name"),
                        "Symbol": idx.get("symbol"),
                        "Last Price": "N/A" if price is None else f"{price:,.2f}",
                    }
                )
            st.table(rows)
        else:
            st.info("No index data available for this exchange.")

        st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    _render_sidebar()
    _render_header()

    country = _render_country_input()
    fetch = st.button("Fetch Data", type="primary")

    if fetch:
        if not country.strip():
            st.warning("Please enter a country name.")
            return

        with st.spinner("Fetching currency, FX rates, stock indices, and maps data…"):
            try:
                profile = build_country_financial_profile(country)
                st.session_state["last_profile"] = profile
                st.session_state.pop("last_error", None)
            except Exception as exc:  # pragma: no cover - defensive
                st.session_state["last_error"] = str(exc)
                st.session_state["last_profile"] = None

    if st.session_state.get("last_error"):
        st.error(st.session_state["last_error"])

    profile = st.session_state.get("last_profile")
    if not profile:
        return

    # ----- Structured output sections -----
    st.markdown("### Results")

    # Country + currency overview
    with st.container():
        col1, col2, col3 = st.columns(3)
        currency = profile.get("currency", {})
        fx = profile.get("exchange_rates", {})

        with col1:
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Country</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='metric-value'>{profile.get('country', 'N/A')}</div>",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            currency_name = currency.get("currency_name") or "Unknown"
            currency_code = currency.get("currency_code") or "N/A"
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Currency</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='metric-value'>{currency_name} ({currency_code})</div>",
                unsafe_allow_html=True,
            )
            if error := currency.get("error"):
                st.caption(f"Lookup warning: {error}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col3:
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>FX Provider</div>", unsafe_allow_html=True)
            provider = fx.get("provider", "currencyapi.com")
            st.markdown(
                f"<div class='metric-value'>{provider}</div>",
                unsafe_allow_html=True,
            )
            if error := fx.get("error"):
                st.caption(f"FX error: {error}")
            st.markdown("</div>", unsafe_allow_html=True)

    # Exchange rates table
    st.markdown("#### Exchange Rates (1 unit of local currency)")
    if "error" in fx and not fx.get("rates"):
        st.warning(fx["error"])
    else:
        _render_exchange_rate_table(fx.get("rates", {}), fx.get("base_currency", "") or currency.get("currency_code", ""))

    # Stock exchanges and indices
    st.markdown("#### Stock Exchanges and Major Indices")
    _render_stock_section(profile.get("stocks", {}))

    # Google Maps section
    maps_link = profile.get("google_maps_link")
    hq_address = profile.get("main_exchange_hq_address")
    st.markdown("#### Main Stock Exchange Headquarters")
    if hq_address:
        st.write(hq_address)
    if maps_link:
        st.markdown(f"[Open in Google Maps]({maps_link})")
    else:
        st.info("No headquarters address available to generate a Maps link.")

    # Optional LLM narrative summary
    st.markdown("#### LLM Summary (Optional)")
    col_left, col_right = st.columns([1, 3])
    with col_left:
        generate = st.checkbox(
            "Generate explanation using LLM",
            value=False,
            help="Uses the selected LLM provider from the sidebar.",
        )
    if generate:
        provider = st.session_state.get("llm_provider", "gemini")
        try:
            with st.spinner(f"Calling {provider} to generate summary…"):
                summary = generate_llm_summary(profile, provider=provider)  # type: ignore[arg-type]
            st.markdown(summary)
        except Exception as exc:  # pragma: no cover - defensive
            st.error(f"Error while generating LLM summary: {exc}")


if __name__ == "__main__":
    main()

