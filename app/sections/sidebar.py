"""Sidebar: weight sliders and filters. Returns what the user picked."""

import streamlit as st

import scoring


def weight_sliders():
    """A preset picker plus one 0-10 slider per criterion."""
    st.sidebar.header("What matters to you?")
    preset = st.sidebar.selectbox("Start from", list(scoring.PRESETS))
    defaults = scoring.PRESETS[preset]

    weights = {}
    for key, (_, _, label) in scoring.CRITERIA.items():
        # Putting the preset in the key resets the sliders when the preset changes
        weights[key] = st.sidebar.slider(label, 0, 10, defaults[key], key=f"{preset}-{key}")
    return weights


def filters(df):
    """Optional filters. Returns the filtered table."""
    st.sidebar.header("Filters")
    types = st.sidebar.multiselect(
        "Type", sorted(df["control_label"].unique()), default=sorted(df["control_label"].unique())
    )
    states = st.sidebar.multiselect("States (empty = all)", sorted(df["state"].unique()))
    min_size = st.sidebar.slider("Minimum undergrads", 0, 20000, 0, step=500)

    keep = df["control_label"].isin(types) & (df["undergrads"].fillna(0) >= min_size)
    if states:
        keep &= df["state"].isin(states)

    with st.sidebar.expander("Financial limits (optional)"):
        st.caption(
            "These are school-level figures, not a personalized aid estimate. "
            "Schools with missing cost data remain included."
        )
        if st.checkbox("Set a maximum average net price"):
            max_net_price = st.number_input(
                "Maximum reported average net price ($)",
                min_value=0,
                max_value=100000,
                value=30000,
                step=2500,
            )
            keep &= df["net_price"].isna() | (df["net_price"] <= max_net_price)

        if st.checkbox("Set a maximum published tuition"):
            max_tuition = st.number_input(
                "Maximum published tuition & fees ($)",
                min_value=0,
                max_value=100000,
                value=30000,
                step=2500,
            )
            keep &= df["sticker_price"].isna() | (df["sticker_price"] <= max_tuition)

    return df[keep]
