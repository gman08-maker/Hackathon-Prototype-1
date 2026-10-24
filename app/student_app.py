"""
Two-step student experience for Rankings vs. Reality.

Run from the project folder:
    streamlit run app/student_app.py
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import config  # noqa: E402
import scoring  # noqa: E402
from sections import about, fragility, map_view, ranking, scatter, value_added  # noqa: E402

st.set_page_config(page_title="College Fit Rankings", page_icon="🎓", layout="wide")

OUTCOME_CRITERIA = ("earnings", "graduation", "mobility", "prestige")
FINANCIAL_CRITERIA = ("affordability", "tuition", "low_debt")


@st.cache_data
def load_results():
    return pd.read_csv(config.RESULTS_CSV)


def collect_inputs(all_schools):
    st.title("Build your college priorities")
    st.write(
        "Choose the outcomes and costs that matter to you. Your choices stay in this "
        "app session and are used to calculate the rankings shown on the next screen."
    )
    st.info(
        "Financial figures are school-level averages, not a personalized aid estimate. "
        "Do not enter sensitive personal or financial information."
    )

    preset = st.selectbox("Start with a ranking style", list(scoring.PRESETS))
    defaults = scoring.PRESETS[preset]

    with st.form("student_characteristics"):
        st.subheader("Student outcomes and characteristics")
        st.caption("Set each weight from 0 (not important) to 10 (very important).")
        weights = {}
        for key in OUTCOME_CRITERIA:
            _, _, label = scoring.CRITERIA[key]
            weights[key] = st.slider(
                label, 0, 10, defaults[key], key=f"{preset}-student-{key}"
            )

        st.subheader("Financial fit")
        st.caption(
            "These financial characteristics are first-class ranking priorities, "
            "alongside student outcomes."
        )
        for key in FINANCIAL_CRITERIA:
            _, _, label = scoring.CRITERIA[key]
            weights[key] = st.slider(
                label, 0, 10, defaults[key], key=f"{preset}-financial-{key}"
            )

        st.markdown("**Optional financial limits**")
        st.caption(
            "Schools missing a reported price remain included. Limits filter the "
            "school list; they do not estimate your personal cost."
        )
        limit_net_price = st.checkbox("Set a maximum average net price")
        max_net_price = st.number_input(
            "Maximum average net price ($)",
            min_value=0,
            max_value=100000,
            value=30000,
            step=2500,
            disabled=not limit_net_price,
        )
        limit_tuition = st.checkbox("Set a maximum published tuition and fees")
        max_tuition = st.number_input(
            "Maximum published tuition and fees ($)",
            min_value=0,
            max_value=100000,
            value=30000,
            step=2500,
            disabled=not limit_tuition,
        )

        st.subheader("School preferences")
        types = st.multiselect(
            "College type",
            sorted(all_schools["control_label"].dropna().unique()),
            default=sorted(all_schools["control_label"].dropna().unique()),
        )
        states = st.multiselect(
            "States (leave empty for all)",
            sorted(all_schools["state"].dropna().unique()),
        )
        min_size = st.slider(
            "Minimum undergraduate enrollment", 0, 20000, 0, step=500
        )

        submitted = st.form_submit_button("Show my rankings", type="primary")

    if submitted:
        st.session_state["student_ranking_inputs"] = {
            "weights": weights,
            "types": types,
            "states": states,
            "min_size": min_size,
            "max_net_price": max_net_price if limit_net_price else None,
            "max_tuition": max_tuition if limit_tuition else None,
        }
        st.session_state["show_student_results"] = True
        st.rerun()


def matching_schools(all_schools, selections):
    keep = (
        all_schools["control_label"].isin(selections["types"])
        & (all_schools["undergrads"].fillna(0) >= selections["min_size"])
    )
    if selections["states"]:
        keep &= all_schools["state"].isin(selections["states"])
    if selections["max_net_price"] is not None:
        keep &= (
            all_schools["net_price"].isna()
            | (all_schools["net_price"] <= selections["max_net_price"])
        )
    if selections["max_tuition"] is not None:
        keep &= (
            all_schools["sticker_price"].isna()
            | (all_schools["sticker_price"] <= selections["max_tuition"])
        )
    return all_schools[keep]


def show_results(all_schools):
    selections = st.session_state["student_ranking_inputs"]
    df = matching_schools(all_schools, selections)

    st.title("Your college rankings")
    if st.button("← Edit my characteristics"):
        st.session_state["show_student_results"] = False
        st.rerun()

    if df.empty:
        st.warning("No schools match these preferences. Edit your inputs to broaden them.")
        return

    pcts = scoring.percentiles(all_schools).loc[df.index]
    weights = selections["weights"]
    scores = scoring.weighted_score(pcts, weights)
    st.caption(
        f"Rankings reflect your selected priorities across {len(df):,} matching schools."
    )

    tabs = st.tabs(
        [
            "Your ranking",
            "Fragility",
            "Prestige vs. outcomes",
            "Overperformers",
            "Map",
            "About & limitations",
        ]
    )
    with tabs[0]:
        table = ranking.render(df, scores)
    with tabs[1]:
        fragility.render(df, pcts, weights)
    with tabs[2]:
        scatter.render(df)
    with tabs[3]:
        value_added.render(df)
    with tabs[4]:
        map_view.render(table)
    with tabs[5]:
        about.render()


def main():
    if not config.RESULTS_CSV.exists():
        st.error("data/results.csv not found. Run `src/clean.py` then `src/analysis.py` first.")
        st.stop()

    all_schools = load_results()
    if st.session_state.get("show_student_results") and "student_ranking_inputs" in st.session_state:
        show_results(all_schools)
    else:
        collect_inputs(all_schools)


main()
