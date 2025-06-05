import streamlit as st
import requests
import pandas as pd
import pymysql
import os
from datetime import datetime

# Connexion MySQL
conn = pymysql.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    ssl={"ssl": {"ssl-mode": "REQUIRED"}}
)

# Créer la table inference_data si elle n'existe pas
create_table_query = """
CREATE TABLE IF NOT EXISTS inference_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    longitude FLOAT,
    latitude FLOAT,
    median_income FLOAT,
    local_hour DATETIME,
    prediction FLOAT
);
"""
with conn.cursor() as cursor:
    cursor.execute(create_table_query)
conn.commit()

st.title('Prédiction du prix des appartements')

median_income = st.number_input("Median Income", min_value=0.0, value=3.5)
latitude = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=34.0)
longitude = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=-118.0)

api_url = "https://housingapp2-h9e3hxbwhzahb5cb.francecentral-01.azurewebsites.net/predict"
password = st.text_input("Mot de passe", type="password")
valid_password = "california"

if st.button('Obtenir la prédiction'):
    if not password:
        st.error("Veuillez entrer le mot de passe pour continuer.")
    elif password != valid_password:
        st.error("Mot de passe incorrect. Veuillez réessayer.")
    else:
        # Appel API
        data = {"features": [longitude, latitude, median_income]}
        response = requests.post(api_url, json=data)

        if response.status_code == 200:
            prediction = response.json()
            prix_pred = prediction['prediction'][0]
            st.write(f"Le prix prédit pour cet appartement est : ${prix_pred:,.2f}")

            # Insertion dans MySQL
            try:
                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO inference_data (longitude, latitude, median_income, local_hour, prediction)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        longitude,
                        latitude,
                        median_income,
                        datetime.now(),
                        prix_pred
                    ))
                conn.commit()
                st.success("Données d'inférence insérées dans MySQL.")
            except Exception as e:
                st.error(f"Erreur lors de l'insertion dans la base de données : {e}")

        else:
            st.error(f"Erreur de prédiction, code : {response.status_code}")

