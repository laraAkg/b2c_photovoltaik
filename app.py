import json

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

from src.geomarketing_app.data import (
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

STRATEGY_HELP = {
    "Balanced": "Ausgewogene Priorisierung fuer eine allgemeine Kampagne.",
    "Technical": "Fokus auf PV-Ertrag und Anzahl geeigneter Daecher.",
    "Premium": "Fokus auf kaufkraftstarke Quartiere mit solider PV-Basis.",
    "Ownership-focused": "Fokus auf Quartiere mit hoeherer Eigentumsquote.",
    "Custom": "Eigene Gewichtung fuer Szenarien oder Praesentationsvarianten.",
}

st.set_page_config(
    page_title="PV Geomarketing Zürich",
    page_icon="☀️",
    layout="wide",
)

# Dashboard styling for a calm, work-focused Streamlit UI.
st.markdown(
    """
    <style>
      .main {padding-top: 0.7rem;}
      .block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1320px;}
      h1, h2, h3 {letter-spacing: 0;}
      .app-eyebrow {
        color: #596579;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.2rem;
      }
      .subtitle {
        color: #435064;
        font-size: 1.04rem;
        line-height: 1.5;
        margin-top: -0.35rem;
        margin-bottom: 1rem;
        max-width: 820px;
      }
      .hint-box {
        background: #f7faf9;
        border: 1px solid #d9e4df;
        border-left: 4px solid #2f855a;
        padding: 0.78rem 0.95rem;
        border-radius: 0.45rem;
        color: #304152;
      }
      .section-title {
        margin-top: 0.65rem;
        margin-bottom: 0.15rem;
        font-weight: 700;
        color: #1f2937;
      }
      div[data-testid="metric-container"] {
        background: #ffffff;
        border: 1px solid #dfe7ef;
        border-radius: 0.45rem;
        padding: 0.72rem 0.82rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
      }
      div[data-testid="stDownloadButton"] button,
      div[data-testid="stButton"] button {
        border-radius: 0.38rem;
        border: 1px solid #b8c5d6;
      }
      section[data-testid="stSidebar"] {
        border-right: 1px solid #e1e7ef;
      }
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


def table_height(row_count: int, max_height: int = 460) -> int:
    return min(max_height, 38 * max(row_count, 1) + 48)


def render_overview(quartier_scored: pd.DataFrame, strassen_df: pd.DataFrame, adressen_df: pd.DataFrame):
    best = quartier_scored.iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Top-Quartier", best["qname"])
    c2.metric("Quartiere", fmt_num(len(quartier_scored)))
    c3.metric("Strassen", fmt_num(strassen_df["lokalisationsname"].nunique()))
    c4.metric("Adressen", fmt_num(len(adressen_df)))

    c5, c6, c7 = st.columns(3)
    c5.metric("PV-Ertrag gesamt", f"{fmt_num(quartier_scored['sum_stromertrag'].sum())} kWh")
    c6.metric("Gute Dächer gesamt", fmt_num(quartier_scored["anzahl_gute_daecher"].sum()))
    c7.metric("Höchster Score", fmt_num(best["targeting_score_dyn"], 3))


def render_db_error(exc: Exception, db_url: str):
    st.error("Die App konnte keine Verbindung zur PostgreSQL/PostGIS-Datenbank herstellen.")
    st.markdown(
        """
        Prüfe kurz diese Punkte:

        1. PostgreSQL läuft lokal.
        2. Die Datenbank `geomarketing` existiert.
        3. PostGIS ist installiert und in der Datenbank aktiviert.
        4. `GEOMARKETING_DB_URL` in `.env` passt zu Port, Benutzer und Datenbank.
        """
    )
    st.code(f"GEOMARKETING_DB_URL={db_url}", language="text")
    with st.expander("Technische Fehlermeldung anzeigen"):
        st.exception(exc)


def score_color(score: float, selected: bool = False) -> list[int]:
    if selected:
        return [247, 148, 29, 210]
    return [int(235 - 145 * score), int(245 - 30 * score), int(255 - 140 * score), 155]


def selected_view_state(
    quartier_df: pd.DataFrame,
    selected_quartier: str | None = None,
    selected_address: pd.Series | None = None,
    street_points: pd.DataFrame | None = None,
) -> pdk.ViewState:
    if selected_address is not None and pd.notna(selected_address.get("roof_lon")):
        return pdk.ViewState(
            latitude=float(selected_address["roof_lat"]),
            longitude=float(selected_address["roof_lon"]),
            zoom=16,
            pitch=0,
        )

    if street_points is not None and not street_points.empty:
        point_df = street_points.dropna(subset=["roof_lon", "roof_lat"])
        if not point_df.empty:
            return pdk.ViewState(
                latitude=float(point_df["roof_lat"].mean()),
                longitude=float(point_df["roof_lon"].mean()),
                zoom=14,
                pitch=0,
            )

    if selected_quartier:
        row = quartier_df.loc[quartier_df["qname"] == selected_quartier]
        if not row.empty and pd.notna(row.iloc[0].get("center_lon")):
            return pdk.ViewState(
                latitude=float(row.iloc[0]["center_lat"]),
                longitude=float(row.iloc[0]["center_lon"]),
                zoom=12.5,
                pitch=0,
            )

    return pdk.ViewState(latitude=47.3769, longitude=8.5417, zoom=11, pitch=0)


def build_dynamic_map(
    quartier_df: pd.DataFrame,
    selected_quartier: str | None = None,
    selected_address: pd.Series | None = None,
    street_points: pd.DataFrame | None = None,
):
    map_df = quartier_df.dropna(subset=["geojson"]).copy()
    if map_df.empty:
        return None

    features = []
    for _, row in map_df.iterrows():
        try:
            geom = json.loads(row["geojson"])
        except Exception:
            continue

        score = float(row["targeting_score_dyn"])
        is_selected = selected_quartier is not None and row["qname"] == selected_quartier

        features.append(
            {
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "qname": row["qname"],
                    "rank": int(row["rank_dyn"]),
                    "score": round(score, 4),
                    "label": row["qname"],
                    "detail": f"Rank {int(row['rank_dyn'])} | Score {score:.3f}",
                    "color": score_color(score, is_selected),
                    "line_color": [203, 88, 20, 255] if is_selected else [79, 88, 103, 170],
                    "line_width": 4 if is_selected else 1,
                },
            }
        )

    if not features:
        return None

    geojson = {"type": "FeatureCollection", "features": features}

    layers = [
        pdk.Layer(
        "GeoJsonLayer",
        data=geojson,
        stroked=True,
        filled=True,
        get_fill_color="properties.color",
        get_line_color="properties.line_color",
        get_line_width="properties.line_width",
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
        )
    ]

    if street_points is not None and not street_points.empty:
        point_df = street_points.dropna(subset=["roof_lon", "roof_lat"]).copy()
        if not point_df.empty:
            point_df["label"] = point_df["adresse"].fillna(point_df["lokalisationsname"]).fillna("Adresse")
            point_df["detail"] = (
                "Stromertrag "
                + point_df["sum_stromertrag"].fillna(0).map(lambda value: f"{value:,.0f}".replace(",", "'"))
                + " kWh"
            )
            layers.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    data=point_df,
                    get_position="[roof_lon, roof_lat]",
                    get_fill_color=[47, 133, 90, 115],
                    get_line_color=[25, 92, 62, 190],
                    get_radius=18,
                    radius_min_pixels=3,
                    radius_max_pixels=18,
                    line_width_min_pixels=1,
                    stroked=True,
                    filled=True,
                    pickable=True,
                )
            )

    if selected_address is not None and pd.notna(selected_address.get("roof_lon")):
        selected_point = pd.DataFrame(
            [
                {
                    "adresse": selected_address.get("adresse"),
                    "label": selected_address.get("adresse"),
                    "detail": f"Stromertrag {fmt_num(selected_address.get('sum_stromertrag'))} kWh",
                    "roof_lon": selected_address.get("roof_lon"),
                    "roof_lat": selected_address.get("roof_lat"),
                    "sum_stromertrag": selected_address.get("sum_stromertrag"),
                }
            ]
        )
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=selected_point,
                get_position="[roof_lon, roof_lat]",
                get_fill_color=[219, 68, 55, 230],
                get_line_color=[120, 32, 24, 255],
                get_radius=28,
                radius_min_pixels=8,
                radius_max_pixels=28,
                line_width_min_pixels=2,
                stroked=True,
                filled=True,
                pickable=True,
            )
        )

    view_state = selected_view_state(quartier_df, selected_quartier, selected_address, street_points)

    return pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        tooltip={
            "html": "<b>{label}</b><br/>{detail}",
        },
    )


def show_quartier_view(quartier_scored: pd.DataFrame, top_n: int):
    st.markdown("### Quartier-Analyse")

    top_quartiers = quartier_scored.head(top_n)
    quartier_options = quartier_scored["qname"].sort_values().tolist()
    selected_q = st.selectbox(
        "Quartier auswählen",
        options=quartier_options,
        index=quartier_options.index(top_quartiers.iloc[0]["qname"]),
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

    st.markdown(
        f"<div class='hint-box'><b>{row['qname']}</b> liegt aktuell auf Rang "
        f"<b>{fmt_num(row['rank_dyn'])}</b>. Der dynamische Score reagiert direkt auf die Gewichtung "
        "in der Sidebar.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<p class='section-title'>Top-Quartiere nach dynamischem Score</p>", unsafe_allow_html=True)
    top_df = top_quartiers.copy()
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

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        height=table_height(len(table_df)),
        column_config={
            "Score": st.column_config.NumberColumn(format="%.3f"),
            "Stromertrag (kWh)": st.column_config.NumberColumn(format="%d"),
            "Median Income (CHF)": st.column_config.NumberColumn(format="%d"),
            "Eigentumsquote (%)": st.column_config.NumberColumn(format="%.1f"),
        },
    )

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

    deck = build_dynamic_map(quartier_scored, selected_quartier=selected_q)
    if deck is not None:
        st.markdown("<p class='section-title'>Kartenansicht des gewählten Quartiers</p>", unsafe_allow_html=True)
        st.pydeck_chart(deck, use_container_width=True)


def show_strassen_view(
    strassen_df: pd.DataFrame,
    adressen_df: pd.DataFrame,
    quartier_scored: pd.DataFrame,
    top_n: int,
):
    st.markdown("### Straßen-Analyse")
    st.markdown(
        "<div class='hint-box'>Die Straßenebene hilft bei mikrogeografischer Vertriebsplanung, "
        "z. B. zur Priorisierung von Außendienstrouten und lokalen Kampagnen.</div>",
        unsafe_allow_html=True,
    )

    sort_options = {
        "Stromertrag": "sum_stromertrag",
        "Gute Dachflächen": "anzahl_gute_dachflaechen",
        "Anzahl Adressen": "anzahl_adressen",
        "Quartier-Score": "avg_quartier_score_dyn",
    }
    sort_label = st.selectbox("Top-Straßen sortieren nach", options=list(sort_options), index=0)
    sort_col = sort_options[sort_label]

    selected_s = st.selectbox(
        "Straße auswählen",
        options=strassen_df["lokalisationsname"].dropna().sort_values().tolist(),
        key="strasse_select",
    )
    row = strassen_df.loc[strassen_df["lokalisationsname"] == selected_s].iloc[0]
    street_points = adressen_df[adressen_df["lokalisationsname"] == selected_s]

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

    deck = build_dynamic_map(
        quartier_scored,
        selected_quartier=street_points["statistisches_quartier"].dropna().iloc[0]
        if not street_points["statistisches_quartier"].dropna().empty
        else None,
        street_points=street_points,
    )
    if deck is not None:
        st.markdown("<p class='section-title'>Kartenansicht der gewählten Straße</p>", unsafe_allow_html=True)
        st.pydeck_chart(deck, use_container_width=True)

    st.markdown(f"<p class='section-title'>Top-Straßen nach {sort_label}</p>", unsafe_allow_html=True)
    top_df = strassen_df.sort_values(sort_col, ascending=False).head(top_n).copy()
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

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        height=table_height(len(table_df)),
        column_config={
            "Stromertrag (kWh)": st.column_config.NumberColumn(format="%d"),
            "Ø Quartier-Score (dyn)": st.column_config.NumberColumn(format="%.3f"),
            "Bester Quartier-Rank (dyn)": st.column_config.NumberColumn(format="%d"),
        },
    )
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
            x=alt.X(f"{sort_col}:Q", title=sort_label),
            y=alt.Y("lokalisationsname:N", sort="-x", title="Straße"),
            tooltip=[
                alt.Tooltip("lokalisationsname:N", title="Straße"),
                alt.Tooltip("sum_stromertrag:Q", title="Stromertrag", format=",.0f"),
                alt.Tooltip("anzahl_gute_dachflaechen:Q", title="Gute Dachflächen", format=",.0f"),
                alt.Tooltip("avg_quartier_score_dyn:Q", title="Ø Quartier-Score", format=".3f"),
            ],
            color=alt.value("#2f855a"),
        )
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)


def show_adressen_view(adressen_df: pd.DataFrame, quartier_scored: pd.DataFrame, top_n: int):
    st.markdown("### Adress- und Haus-Analyse")
    st.markdown(
        "<div class='hint-box'>Adressen bilden die operative Lead-Ebene für direkte Vertriebskontakte "
        "und gebäudebezogene Angebotspriorisierung.</div>",
        unsafe_allow_html=True,
    )

    f1, f2 = st.columns(2)
    quartiers = ["Alle"] + adressen_df["statistisches_quartier"].dropna().sort_values().unique().tolist()
    selected_quartier = f1.selectbox("Quartier filtern", options=quartiers, index=0)

    filtered_df = adressen_df.copy()
    if selected_quartier != "Alle":
        filtered_df = filtered_df[filtered_df["statistisches_quartier"] == selected_quartier]

    streets = ["Alle"] + filtered_df["lokalisationsname"].dropna().sort_values().unique().tolist()
    selected_street = f2.selectbox("Straße filtern", options=streets, index=0)
    if selected_street != "Alle":
        filtered_df = filtered_df[filtered_df["lokalisationsname"] == selected_street]

    if filtered_df.empty:
        st.warning("Keine Adressen für diese Filterkombination gefunden.")
        return

    st.caption(f"{fmt_num(len(filtered_df))} passende Adressen")

    options_df = filtered_df.copy()
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

    deck = build_dynamic_map(
        quartier_scored,
        selected_quartier=row.get("statistisches_quartier"),
        selected_address=row,
        street_points=filtered_df if selected_street != "Alle" else None,
    )
    if deck is not None:
        st.markdown("<p class='section-title'>Kartenansicht der gewählten Adresse</p>", unsafe_allow_html=True)
        st.pydeck_chart(deck, use_container_width=True)

    st.markdown("<p class='section-title'>Top-Adressen nach Stromertrag</p>", unsafe_allow_html=True)
    top_df = filtered_df.sort_values("sum_stromertrag", ascending=False).head(top_n).copy()
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

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        height=table_height(len(table_df)),
        column_config={
            "Stromertrag (kWh)": st.column_config.NumberColumn(format="%d"),
            "Quartier-Score (dyn)": st.column_config.NumberColumn(format="%.3f"),
            "Quartier-Rank (dyn)": st.column_config.NumberColumn(format="%d"),
        },
    )
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
    st.markdown("<div class='app-eyebrow'>B2C Photovoltaik</div>", unsafe_allow_html=True)
    st.title("Geomarketing-Tool für Photovoltaik in Zürich")
    st.markdown(
        "<p class='subtitle'>Priorisierung profitabler Vertriebsgebiete auf Quartier-, Straßen- und Adressebene. "
        "Der Score verbindet technisches PV-Potenzial mit demografischer Attraktivität.</p>",
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Analyse")
        mode = st.radio("Ebene", options=["Quartier", "Straße", "Adresse"], horizontal=False)

        strategy = st.selectbox(
            "Strategie-Modus",
            options=["Balanced", "Technical", "Premium", "Ownership-focused", "Custom"],
            index=0,
        )
        st.caption(STRATEGY_HELP[strategy])

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

        top_n = st.select_slider("Top-N", options=[5, 10, 20, 50], value=10)
        st.divider()
        st.caption("Datenquelle")
        st.code(get_db_url(), language="text")

    db_url = get_db_url()
    with st.spinner("Lade Daten aus der Geomarketing-Datenbank..."):
        try:
            quartier_df = fetch_quartier_data(db_url)
            strassen_df = fetch_strassen_data(db_url)
            adressen_df = fetch_adressen_data(db_url)
        except Exception as exc:
            render_db_error(exc, db_url)
            st.stop()

    quartier_scored = compute_quartier_scores(quartier_df, weights)
    strassen_ctx, adressen_ctx = enrich_with_dynamic_quartier_context(
        strassen_df, adressen_df, quartier_scored
    )

    render_overview(quartier_scored, strassen_ctx, adressen_ctx)
    st.divider()

    if mode == "Quartier":
        show_quartier_view(quartier_scored, top_n)
    elif mode == "Straße":
        show_strassen_view(strassen_ctx, adressen_ctx, quartier_scored, top_n)
    else:
        show_adressen_view(adressen_ctx, quartier_scored, top_n)


if __name__ == "__main__":
    main()
