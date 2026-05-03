import pandas as pd
from sqlalchemy import create_engine, text

from src.geomarketing_app.data import get_db_url

# --------------------------------------------------
# 1) Datenbankverbindung
# --------------------------------------------------
engine = create_engine(get_db_url(), pool_pre_ping=True)

# --------------------------------------------------
# 2) User-Gewichte einlesen
# --------------------------------------------------
print("Gib die Gewichte für den Targeting Score ein.")
print("Die Summe muss 100 ergeben.\n")

w_strom = float(input("Gewicht Stromertrag (%): "))
w_daecher = float(input("Gewicht gute Dächer (%): "))
w_income = float(input("Gewicht Einkommen (%): "))
w_eigentum = float(input("Gewicht Eigentumsquote (%): "))

weight_sum = w_strom + w_daecher + w_income + w_eigentum

if weight_sum != 100:
    raise ValueError(f"Die Summe der Gewichte ist {weight_sum}, nicht 100.")

# Auf 0-1 umrechnen
w_strom /= 100
w_daecher /= 100
w_income /= 100
w_eigentum /= 100

# --------------------------------------------------
# 3) Input-Tabelle laden
# --------------------------------------------------
query = """
SELECT
    id,
    qnr,
    qname,
    kname,
    median_income::numeric AS median_income,
    eigentumsquote::numeric AS eigentumsquote,
    anzahl_gute_daecher,
    sum_dachflaeche,
    sum_stromertrag,
    avg_stromertrag
FROM mart.quartier_metrics_full
ORDER BY qname;
"""

df = pd.read_sql(query, engine)

# --------------------------------------------------
# 4) Min-Max-Normalisierung
# --------------------------------------------------
def minmax(series: pd.Series) -> pd.Series:
    smin = series.min()
    smax = series.max()
    if smax == smin:
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - smin) / (smax - smin)

df["stromertrag_norm"] = minmax(df["sum_stromertrag"].astype(float))
df["daecher_norm"] = minmax(df["anzahl_gute_daecher"].astype(float))
df["income_norm"] = minmax(df["median_income"].astype(float))
df["eigentum_norm"] = minmax(df["eigentumsquote"].astype(float))

# --------------------------------------------------
# 5) Score berechnen
# --------------------------------------------------
df["targeting_score"] = (
    w_strom * df["stromertrag_norm"] +
    w_daecher * df["daecher_norm"] +
    w_income * df["income_norm"] +
    w_eigentum * df["eigentum_norm"]
)

# Ranking
df = df.sort_values("targeting_score", ascending=False).reset_index(drop=True)
df["rank"] = df.index + 1

# --------------------------------------------------
# 6) Ergebnistabelle ohne Geometrie schreiben
# --------------------------------------------------
result = df[[
    "id", "qnr", "qname", "kname",
    "median_income", "eigentumsquote",
    "anzahl_gute_daecher", "sum_dachflaeche", "sum_stromertrag", "avg_stromertrag",
    "stromertrag_norm", "daecher_norm", "income_norm", "eigentum_norm",
    "targeting_score", "rank"
]]

result.to_sql(
    "quartier_targeting_results",
    engine,
    schema="mart",
    if_exists="replace",
    index=False
)

# --------------------------------------------------
# 7) Map-Tabelle mit Geometrie erzeugen
# --------------------------------------------------
sql_map = """
DROP TABLE IF EXISTS mart.quartier_targeting_results_map;

CREATE TABLE mart.quartier_targeting_results_map AS
SELECT
    t.*,
    q.geom
FROM mart.quartier_targeting_results t
LEFT JOIN core.quartiere_plus q
  ON t.qname = q.qname;
"""

with engine.begin() as conn:
    conn.execute(text(sql_map))

# --------------------------------------------------
# 8) Top 10 anzeigen
# --------------------------------------------------
print("\nTop 10 Quartiere:\n")
print(
    df[[
        "rank", "qname", "targeting_score",
        "sum_stromertrag", "anzahl_gute_daecher",
        "median_income", "eigentumsquote"
    ]].head(10)
)

print("\nFertig: Ergebnisse wurden nach mart.quartier_targeting_results und mart.quartier_targeting_results_map geschrieben.")
