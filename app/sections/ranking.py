"""Tab: the live re-ranked table based on the user's weights."""

import streamlit as st

import config

# How each column shows up in the table
COLUMNS = {
    "your_rank": st.column_config.NumberColumn("Your rank"),
    "prestige_rank": st.column_config.NumberColumn("Prestige rank"),
    "change": st.column_config.NumberColumn("Moved", help="Prestige rank minus your rank. Positive = moved up."),
    "name": st.column_config.TextColumn("School", width="large"),
    "state": "State",
    "control_label": "Type",
    "score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.0f"),
    "net_price": st.column_config.NumberColumn("Net price ($)", format="localized"),
    "sticker_price": st.column_config.NumberColumn("Published tuition & fees ($)", format="localized"),
    "grad_pct": st.column_config.NumberColumn("Grad rate", format="%.0f%%"),
    "pell_grad_pct": st.column_config.NumberColumn("Pell grad rate", format="%.0f%%"),
    "earnings_10yr": st.column_config.NumberColumn("Earnings ($)", format="localized"),
    "median_debt": st.column_config.NumberColumn("Median debt ($)", format="localized"),
}


def build_table(df, scores):
    """Add rank columns and percent columns that are easy to read."""
    t = df.assign(score=scores)
    t["your_rank"] = t["score"].rank(ascending=False, method="first").astype(int)
    t["prestige_rank"] = t["prestige_score"].rank(ascending=False, method="first").astype(int)
    t["change"] = t["prestige_rank"] - t["your_rank"]
    t["grad_pct"] = t["grad_rate"] * 100
    t["pell_grad_pct"] = t["pell_grad_rate"] * 100
    return t.sort_values("your_rank")


def show_bu(table):
    """Three headline numbers for Boston University."""
    bu = table[table["unitid"] == config.BU_UNITID]
    if bu.empty:
        st.caption("Boston University is hidden by the current filters.")
        return
    bu = bu.iloc[0]
    a, b, c = st.columns(3)
    a.metric("Boston University: your rank", f"#{bu['your_rank']} of {len(table)}")
    b.metric("BU: prestige rank", f"#{bu['prestige_rank']}")
    c.metric("BU: score", f"{bu['score']:.0f} / 100")


def render(df, scores):
    st.subheader("Your ranking")
    st.write(
        "Schools re-ranked by the weights in the sidebar. **Moved** compares your "
        "rank with a prestige-only rank."
    )
    table = build_table(df, scores)
    show_bu(table)
    n = st.slider("Show top", 10, 200, 50, step=10)
    st.dataframe(
        table.head(n)[list(COLUMNS)], column_config=COLUMNS,
        hide_index=True, width="stretch", height=600,
    )
    return table
