import json

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

from app_utils import (
    STRATEGY_WEIGHTS,
    compute_quartier_scores,
    enrich_with_dynamic_quartier_context,
    get_db_url,
    get_engine,
    load_adressen_data,
    load_quartier_data,
    load_strassen_data,
    normalize_weights,
)

st.set_page_config(
    page_title="Geomarketing-Tool PV Zürich",
    page_icon="☀️",
    layout="wide",
)

# Schlankes Styling für eine aufgeräumte Dashboard-Optik.
st.markdown(
    """
    <style>
      .main {padding-top: 0.8rem;}
      .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
      .subtitle {color: #4a5568; font-size: 1.05rem; margin-top: -0.45rem; margin-bottom: 0.8rem;}
      .hint-box {background:#f6f8fb; border:1px solid #e2e8f0; padding:0.75rem 0.9rem; border-radius:0.6rem;}
      .section-title {margin-top: 0.4rem; margin-bottom: 0.1rem; font-weight: 600;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_cached_engine(db_url: str):
    return get_engine(db_url)


@st.cache_data(ttl=600)
def fetch_quartier_data(db_url: str) -> pd.DataFrame:
    engine = get_cached_engine(db_url)
    return load_quartier_data(engine)


@st.cache_data(ttl=600)
def fetch_strassen_data(db_url: str) -> pd.DataFrame:
    engine = get_cached_engine(db_url)
    return load_strassen_data(engine)


@st.cache_data(ttl=600)
def fetch_adressen_data(db_url: str) -> pd.DataFrame:
    engine = get_cached_engine(db_url)
    return load_adressen_data(engine)


def fmt_num(value, decimals: int = 0) -> str:
    if pd.isna(value):
        return "-"
    if decimals == 0:
        return f"{value:,.0f}".replace(",", "'")
    return f"{value:,.{decimals}f}".replace(",", "'")


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def build_quartier_map(df: pd.DataFrame):
    map_df = df.dropna(subset=["geojson"]).copy()
    if map_df.empty:
        return None

    features = []
    for _, row in map_df.iterrows():
        try:
            geom = json.loads(row["geojson"])
        except Exception:
            continue

        score = float(row["targeting_score_dyn"])
        color = [int(235 - 145 * score), int(245 - 30 * score), int(255 - 140 * score), 160]

        features.append(
            {
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "qname": row["qname"],
                    "rank": int(row["rank_dyn"]),
                    "score": round(score, 4),
                    "color": color,
                },
            }
        )

    if not features:
        return None

    geojson = {"type": "FeatureCollection", "features": features}

    layer = pdk.Layer(
        "GeoJsonLayer",
        data=geojson,
        stroked=True,
        filled=True,
        get_fill_color="properties.color",
        get_line_color=[90, 98, 110],
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(latitude=47.3769, longitude=8.5417, zoom=11, pitch=0)

    return pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"html": "<b>{qname}</b><br/>Rank: {rank}<br/>Score: {score}"},
    )


def show_quartier_view(quartier_scored: pd.DataFrame, top_n: int):
    st.markdown("### Quartier-Analyse")

    selected_q = st.selectbox(
        "Quartier auswählen",
        options=quartier_scored["qname"].sort_values().tolist(),
        key="quartier_select",
    )

    row = quartier_scored.loc[quartier_scored["qname"] == selected_q].iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Dynamischer Rank", fmt_num(row["rank_dyn"]))
    c2.metric("Dynamischer Score", fmt_num(row["targeting_score_dyn"], 3))
    c3.metric("Median Income", f"CHF {fmt_num(row['median_income'])}")

    c4, c5, c6 = st.columns(3)
    c4.metric("Eigentumsquote", f"{fmt_num(row['eigentumsquote'], 1)} %")
    c5.metric("Gute Dächer", fmt_num(row["anzahl_gute_daecher"]))
    c6.metric("Summe Stromertrag", f"{fmt_num(row['sum_stromertrag'])} kWh")

    st.markdown("<p class='section-title'>Top-Quartiere nach dynamischem Score</p>", unsafe_allow_html=True)
    top_df = quartier_scored.head(top_n).copy()
    table_df = top_df[
        [
            "rank_dyn",
            "qname",
            "kname",
            "targeting_score_dyn",
            "sum_stromertrag",
            "anzahl_gute_daecher",
            "median_income",
            "eigentumsquote",
        ]
    ].rename(
        columns={
            "rank_dyn": "Rank",
            "qname": "Quartier",
            "kname": "Stadtkreis",
            "targeting_score_dyn": "Score",
            "sum_stromertrag": "Stromertrag (kWh)",
            "anzahl_gute_daecher": "Gute Dächer",
            "median_income": "Median Income (CHF)",
            "eigentumsquote": "Eigentumsquote (%)",
        }
    )

    st.dataframe(table_df, use_container_width=True, hide_index=True)

    st.download_button(
        "Top-Quartiere als CSV herunterladen",
        data=to_csv_bytes(table_df),
        file_name=f"top_quartiere_{top_n}.csv",
        mime="text/csv",
    )

    chart = (
        alt.Chart(top_df)
        .mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
        .encode(
            x=alt.X("targeting_score_dyn:Q", title="Dynamischer Score"),
            y=alt.Y("qname:N", sort="-x", title="Quartier"),
            tooltip=[
                alt.Tooltip("qname:N", title="Quartier"),
                alt.Tooltip("rank_dyn:Q", title="Rank"),
                alt.Tooltip("targeting_score_dyn:Q", title="Score", format=".3f"),
            ],
            color=alt.value("#2b6cb0"),
        )
        .properties(height=300)
    )

    st.altair_chart(chart, use_container_width=True)

    deck = build_quartier_map(quartier_scored)
    if deck is not None:
        st.markdown("<p class='section-title'>Kartenansicht (dynamischer Quartier-Score)</p>", unsafe_allow_html=True)
        st.pydeck_chart(deck, use_container_width=True)


def show_strassen_view(strassen_df: pd.DataFrame, top_n: int):
    st.markdown("### Straßen-Analyse")
    st.markdown(
        "<div class='hint-box'>Die Straßenebene hilft bei mikrogeografischer Vertriebsplanung, "
        "z. B. zur Priorisierung von Außendienstrouten und lokalen Kampagnen.</div>",
        unsafe_allow_html=True,
    )

    selected_s = st.selectbox(
        "Straße auswählen",
        options=strassen_df["lokalisationsname"].dropna().sort_values().tolist(),
        key="strasse_select",
    )
    row = strassen_df.loc[strassen_df["lokalisationsname"] == selected_s].iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Anzahl Adressen", fmt_num(row["anzahl_adressen"]))
    c2.metric("Gute Dachflächen", fmt_num(row["anzahl_gute_dachflaechen"]))
    c3.metric("Summe Stromertrag", f"{fmt_num(row['sum_stromertrag'])} kWh")

    c4, c5, c6 = st.columns(3)
    c4.metric("Beste Klasse", row["beste_klasse"] if pd.notna(row["beste_klasse"]) else "-")
    c5.metric(
        "Ø Quartier-Score (dyn)",
        fmt_num(row.get("avg_quartier_score_dyn"), 3) if pd.notna(row.get("avg_quartier_score_dyn")) else "-",
    )
    c6.metric(
        "Bester Quartier-Rank (dyn)",
        fmt_num(row.get("best_quartier_rank_dyn")) if pd.notna(row.get("best_quartier_rank_dyn")) else "-",
    )

    st.markdown("<p class='section-title'>Top-Straßen nach Stromertrag</p>", unsafe_allow_html=True)
    top_df = strassen_df.sort_values("sum_stromertrag", ascending=False).head(top_n).copy()
    table_df = top_df[
        [
            "lokalisationsname",
            "sum_stromertrag",
            "anzahl_adressen",
            "anzahl_gute_dachflaechen",
            "beste_klasse",
            "avg_quartier_score_dyn",
            "best_quartier_rank_dyn",
        ]
    ].rename(
        columns={
            "lokalisationsname": "Straße",
            "sum_stromertrag": "Stromertrag (kWh)",
            "anzahl_adressen": "Anzahl Adressen",
            "anzahl_gute_dachflaechen": "Gute Dachflächen",
            "beste_klasse": "Beste Klasse",
            "avg_quartier_score_dyn": "Ø Quartier-Score (dyn)",
            "best_quartier_rank_dyn": "Bester Quartier-Rank (dyn)",
        }
    )

    st.dataframe(table_df, use_container_width=True, hide_index=True)
    st.download_button(
        "Top-Straßen als CSV herunterladen",
        data=to_csv_bytes(table_df),
        file_name=f"top_strassen_{top_n}.csv",
        mime="text/csv",
    )

    chart = (
        alt.Chart(top_df)
        .mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
        .encode(
            x=alt.X("sum_stromertrag:Q", title="Stromertrag (kWh)"),
            y=alt.Y("lokalisationsname:N", sort="-x", title="Straße"),
            tooltip=[
                alt.Tooltip("lokalisationsname:N", title="Straße"),
                alt.Tooltip("sum_stromertrag:Q", title="Stromertrag", format=",.0f"),
            ],
            color=alt.value("#2f855a"),
        )
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)


def show_adressen_view(adressen_df: pd.DataFrame, top_n: int):
    st.markdown("### Adress- und Haus-Analyse")
    st.markdown(
        "<div class='hint-box'>Adressen bilden die operative Lead-Ebene für direkte Vertriebskontakte "
        "und gebäudebezogene Angebotspriorisierung.</div>",
        unsafe_allow_html=True,
    )

    options_df = adressen_df.copy()
    options_df["adresse_label"] = (
        options_df["adresse"].fillna("Unbekannt")
        + " | EGID "
        + options_df["gwr_egid"].fillna("-").astype(str)
    )

    selected_label = st.selectbox(
        "Adresse auswählen",
        options=options_df["adresse_label"].sort_values().tolist(),
        key="adresse_select",
    )
    row = options_df.loc[options_df["adresse_label"] == selected_label].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Adresse", row["adresse"] if pd.notna(row["adresse"]) else "-")
    c2.metric("Quartier", row["statistisches_quartier"] if pd.notna(row["statistisches_quartier"]) else "-")
    c3.metric("Stadtkreis", row["stadtkreis"] if pd.notna(row["stadtkreis"]) else "-")
    c4.metric("Beste Klasse", row["beste_klasse"] if pd.notna(row["beste_klasse"]) else "-")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Gute Dachflächen", fmt_num(row["anzahl_gute_dachflaechen"]))
    c6.metric("Summe Stromertrag", f"{fmt_num(row['sum_stromertrag'])} kWh")
    c7.metric(
        "Quartier-Score (dyn)",
        fmt_num(row.get("targeting_score_dyn"), 3) if pd.notna(row.get("targeting_score_dyn")) else "-",
    )
    c8.metric(
        "Quartier-Rank (dyn)",
        fmt_num(row.get("rank_dyn")) if pd.notna(row.get("rank_dyn")) else "-",
    )

    st.markdown("<p class='section-title'>Top-Adressen nach Stromertrag</p>", unsafe_allow_html=True)
    top_df = adressen_df.sort_values("sum_stromertrag", ascending=False).head(top_n).copy()
    table_df = top_df[
        [
            "adresse",
            "lokalisationsname",
            "sum_stromertrag",
            "anzahl_gute_dachflaechen",
            "beste_klasse",
            "statistisches_quartier",
            "targeting_score_dyn",
            "rank_dyn",
        ]
    ].rename(
        columns={
            "adresse": "Adresse",
            "lokalisationsname": "Straße",
            "sum_stromertrag": "Stromertrag (kWh)",
            "anzahl_gute_dachflaechen": "Gute Dachflächen",
            "beste_klasse": "Beste Klasse",
            "statistisches_quartier": "Quartier",
            "targeting_score_dyn": "Quartier-Score (dyn)",
            "rank_dyn": "Quartier-Rank (dyn)",
        }
    )

    st.dataframe(table_df, use_container_width=True, hide_index=True)
    st.download_button(
        "Top-Adressen als CSV herunterladen",
        data=to_csv_bytes(table_df),
        file_name=f"top_adressen_{top_n}.csv",
        mime="text/csv",
    )

    same_street = adressen_df[adressen_df["lokalisationsname"] == row["lokalisationsname"]]
    if not same_street.empty:
        st.markdown("<p class='section-title'>Weitere Adressen in derselben Straße</p>", unsafe_allow_html=True)
        same_street_df = same_street.sort_values("sum_stromertrag", ascending=False).head(25)[
            [
                "adresse",
                "sum_stromertrag",
                "anzahl_gute_dachflaechen",
                "beste_klasse",
                "targeting_score_dyn",
                "rank_dyn",
            ]
        ].rename(
            columns={
                "adresse": "Adresse",
                "sum_stromertrag": "Stromertrag (kWh)",
                "anzahl_gute_dachflaechen": "Gute Dachflächen",
                "beste_klasse": "Beste Klasse",
                "targeting_score_dyn": "Quartier-Score (dyn)",
                "rank_dyn": "Quartier-Rank (dyn)",
            }
        )
        st.dataframe(same_street_df, use_container_width=True, hide_index=True)


def main():
    st.title("Geomarketing-Tool für Photovoltaik in Zürich")
    st.markdown(
        "<p class='subtitle'>Priorisierung profitabler Vertriebsgebiete auf Quartier-, Straßen- und Adressebene</p>",
        unsafe_allow_html=True,
    )
    st.write(
        "Diese App kombiniert technische PV-Eignung (Dachflächen und Stromertrag) "
        "mit demografischen Faktoren, um Vertriebsgebiete datenbasiert zu priorisieren."
    )

    with st.sidebar:
        st.header("Steuerung")
        mode = st.radio("Ebene", options=["Quartier", "Straße", "Adresse"], horizontal=False)

        strategy = st.selectbox(
            "Strategie-Modus",
            options=["Balanced", "Technical", "Premium", "Ownership-focused", "Custom"],
            index=0,
        )

        if strategy == "Custom":
            st.caption("Eigene Gewichtung (automatisch normiert)")
            w_strom = st.slider("Stromertrag", min_value=0, max_value=100, value=45, step=5)
            w_daecher = st.slider("Gute Dächer", min_value=0, max_value=100, value=25, step=5)
            w_income = st.slider("Einkommen", min_value=0, max_value=100, value=15, step=5)
            w_eigentum = st.slider("Eigentumsquote", min_value=0, max_value=100, value=15, step=5)
            raw_weights = {
                "stromertrag": w_strom,
                "daecher": w_daecher,
                "income": w_income,
                "eigentum": w_eigentum,
            }
        else:
            raw_weights = STRATEGY_WEIGHTS[strategy]
            st.caption(
                "Gewichte: "
                f"Strom {raw_weights['stromertrag']} / "
                f"Dächer {raw_weights['daecher']} / "
                f"Income {raw_weights['income']} / "
                f"Eigentum {raw_weights['eigentum']}"
            )

        weights, raw_sum = normalize_weights(raw_weights)
        st.caption(
            "Normierte Gewichte: "
            f"{weights['stromertrag']*100:.1f} / "
            f"{weights['daecher']*100:.1f} / "
            f"{weights['income']*100:.1f} / "
            f"{weights['eigentum']*100:.1f}"
        )
        if strategy == "Custom" and raw_sum != 100:
            st.info(f"Hinweis: Die Eingabe summiert sich zu {raw_sum:.0f}. Werte wurden automatisch normiert.")

        top_n = st.select_slider("Top-N", options=[5, 10, 20], value=10)

    db_url = get_db_url()
    with st.spinner("Lade Daten aus der Geomarketing-Datenbank..."):
        try:
            quartier_df = fetch_quartier_data(db_url)
            strassen_df = fetch_strassen_data(db_url)
            adressen_df = fetch_adressen_data(db_url)
        except Exception as exc:
            st.error("Fehler beim Laden aus PostgreSQL/PostGIS. Bitte Verbindung prüfen.")
            st.exception(exc)
            st.stop()

    quartier_scored = compute_quartier_scores(quartier_df, weights)
    strassen_ctx, adressen_ctx = enrich_with_dynamic_quartier_context(
        strassen_df, adressen_df, quartier_scored
    )

    if mode == "Quartier":
        show_quartier_view(quartier_scored, top_n)
    elif mode == "Straße":
        show_strassen_view(strassen_ctx, top_n)
    else:
        show_adressen_view(adressen_ctx, top_n)


if __name__ == "__main__":
    main()
