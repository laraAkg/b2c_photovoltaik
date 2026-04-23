import os
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

DEFAULT_DB_URL = "postgresql+psycopg2://lara@localhost:5433/geomarketing"

STRATEGY_WEIGHTS = {
    "Balanced": {
        "stromertrag": 45,
        "daecher": 25,
        "income": 15,
        "eigentum": 15,
    },
    "Technical": {
        "stromertrag": 60,
        "daecher": 25,
        "income": 10,
        "eigentum": 5,
    },
    "Premium": {
        "stromertrag": 30,
        "daecher": 20,
        "income": 30,
        "eigentum": 20,
    },
    "Ownership-focused": {
        "stromertrag": 35,
        "daecher": 20,
        "income": 10,
        "eigentum": 35,
    },
}


def get_db_url() -> str:
    """Liest die DB-URL aus der Umgebung oder nutzt den lokalen Standard."""
    return os.getenv("GEOMARKETING_DB_URL", DEFAULT_DB_URL)


def get_engine(db_url: str):
    """Erzeugt eine robuste SQLAlchemy-Engine."""
    return create_engine(db_url, pool_pre_ping=True)


def load_quartier_data(engine) -> pd.DataFrame:
    """Lädt Quartierdaten inkl. GeoJSON-Geometrie für eine optionale Kartenansicht."""
    query = text(
        """
        SELECT
            qname,
            qnr,
            kname,
            median_income::float AS median_income,
            eigentumsquote::float AS eigentumsquote,
            anzahl_gute_daecher::float AS anzahl_gute_daecher,
            sum_dachflaeche::float AS sum_dachflaeche,
            sum_stromertrag::float AS sum_stromertrag,
            avg_stromertrag::float AS avg_stromertrag,
            CASE
                WHEN geom IS NOT NULL THEN ST_AsGeoJSON(ST_CurveToLine(geom))
            END AS geojson
        FROM mart.quartier_targeting_results_map
        ORDER BY qname;
        """
    )
    return pd.read_sql(query, engine)


def load_strassen_data(engine) -> pd.DataFrame:
    """Lädt die aggregierte Straßenebene."""
    query = text(
        """
        SELECT
            lokalisationsname,
            anzahl_adressen::float AS anzahl_adressen,
            anzahl_gute_dachflaechen::float AS anzahl_gute_dachflaechen,
            sum_dachflaeche::float AS sum_dachflaeche,
            sum_stromertrag::float AS sum_stromertrag,
            beste_klasse,
            avg_quartier_score::float AS avg_quartier_score,
            best_quartier_rank::float AS best_quartier_rank
        FROM mart.strassen_mit_pv
        ORDER BY lokalisationsname;
        """
    )
    return pd.read_sql(query, engine)


def load_adressen_data(engine) -> pd.DataFrame:
    """Lädt die operative Adress-/Haus-Ebene."""
    query = text(
        """
        SELECT
            adresse,
            lokalisationsname,
            hausnummer,
            gwr_egid,
            stadtkreis,
            statistisches_quartier,
            anzahl_gute_dachflaechen::float AS anzahl_gute_dachflaechen,
            sum_dachflaeche::float AS sum_dachflaeche,
            sum_stromertrag::float AS sum_stromertrag,
            beste_klasse,
            targeting_score::float AS targeting_score,
            rank::float AS rank
        FROM mart.adressen_mit_pv
        ORDER BY adresse;
        """
    )
    return pd.read_sql(query, engine)


def minmax(series: pd.Series) -> pd.Series:
    """Min-Max-Normalisierung mit sicherem Fallback für konstante Spalten."""
    s = pd.to_numeric(series, errors="coerce").fillna(0.0)
    s_min = float(s.min())
    s_max = float(s.max())
    if np.isclose(s_max, s_min):
        return pd.Series(0.0, index=s.index)
    return (s - s_min) / (s_max - s_min)


def normalize_weights(raw_weights: Dict[str, float]) -> Tuple[Dict[str, float], float]:
    """Normiert beliebige Rohgewichte auf eine Summe von 1.0.

    Rückgabe: (normierte Gewichte, Rohsumme)
    """
    total = float(sum(raw_weights.values()))
    if total <= 0:
        # Sicherer Fallback: gleich verteilen
        return {
            "stromertrag": 0.25,
            "daecher": 0.25,
            "income": 0.25,
            "eigentum": 0.25,
        }, total

    normalized = {key: float(value) / total for key, value in raw_weights.items()}
    return normalized, total


def compute_quartier_scores(
    quartier_df: pd.DataFrame, weights: Dict[str, float]
) -> pd.DataFrame:
    """Berechnet dynamische Quartier-Scores und Ranking basierend auf Gewichten."""
    df = quartier_df.copy()

    df["stromertrag_norm_dyn"] = minmax(df["sum_stromertrag"])
    df["daecher_norm_dyn"] = minmax(df["anzahl_gute_daecher"])
    df["income_norm_dyn"] = minmax(df["median_income"])
    df["eigentum_norm_dyn"] = minmax(df["eigentumsquote"])

    df["targeting_score_dyn"] = (
        weights["stromertrag"] * df["stromertrag_norm_dyn"]
        + weights["daecher"] * df["daecher_norm_dyn"]
        + weights["income"] * df["income_norm_dyn"]
        + weights["eigentum"] * df["eigentum_norm_dyn"]
    )

    df = df.sort_values("targeting_score_dyn", ascending=False).reset_index(drop=True)
    df["rank_dyn"] = df.index + 1
    return df


def enrich_with_dynamic_quartier_context(
    strassen_df: pd.DataFrame,
    adressen_df: pd.DataFrame,
    quartier_scored_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Ergänzt Straßen- und Adressdaten um dynamischen Quartier-Score/-Rank-Kontext."""
    quart_ctx = quartier_scored_df[["qname", "targeting_score_dyn", "rank_dyn"]].rename(
        columns={"qname": "statistisches_quartier"}
    )

    adressen = adressen_df.merge(quart_ctx, on="statistisches_quartier", how="left")

    street_ctx = (
        adressen.groupby("lokalisationsname", dropna=False)
        .agg(
            avg_quartier_score_dyn=("targeting_score_dyn", "mean"),
            best_quartier_rank_dyn=("rank_dyn", "min"),
        )
        .reset_index()
    )

    strassen = strassen_df.merge(street_ctx, on="lokalisationsname", how="left")
    return strassen, adressen
