import os
import urllib.parse
import pymysql
import pandas as pd
from sqlalchemy import create_engine

from evidently import Dataset, Report
from evidently.presets import DataSummaryPreset, DataDriftPreset
from evidently.ui.workspace import CloudWorkspace
from evidently import DataDefinition

# ─── 1. Paramètres de Connexion MySQL ─────────────────────────────────────────

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "ssl": {"ssl": {"ssl-mode": "REQUIRED"}},
}

# ─── 2. Connexion MySQL & Chargement des Données ──────────────────────────────

def get_dataframe_from_query(query: str) -> pd.DataFrame:
    conn = pymysql.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        port=DB_CONFIG["port"],
        ssl=DB_CONFIG["ssl"]
    )
    df = pd.read_sql(query, conn)
    conn.close()
    return df

train_df = get_dataframe_from_query("SELECT * FROM train_data;")
inference_df = get_dataframe_from_query("SELECT * FROM inference_data;")

# ─── 3. Définir les Datasets Evidently ────────────────────────────────────────

columns = ["longitude", "latitude", "median_income"]
datetime_column = "local_hour"

train_definition = DataDefinition(
    numerical_columns=columns,
    datetime_columns=[datetime_column],
    timestamp=datetime_column,
)

inference_definition = DataDefinition(
    numerical_columns=columns,
    datetime_columns=[datetime_column],
    timestamp=datetime_column,
)

train_data = Dataset.from_pandas(train_df, data_definition=train_definition)
inference_data = Dataset.from_pandas(inference_df, data_definition=inference_definition)

# ─── 4. Générer le Rapport Evidently ──────────────────────────────────────────

report = Report(
    metrics=[DataSummaryPreset(), DataDriftPreset()],
    include_tests=True
)

my_report = report.run(train_data, inference_data)

# ─── 5. Publier dans Evently IA (Cloud Evidently) ─────────────────────────────

workspace = CloudWorkspace(
    token=os.getenv("EVENTLY_TOKEN"),
    url=os.getenv("EVENTLY_URL")
)

project = workspace.get_project("019735f0-424a-7dc8-a160-1178a72232b6")
workspace.add_run(project.id, my_report)

print("Rapport Evidently généré et publié avec succès.")
