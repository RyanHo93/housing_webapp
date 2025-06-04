import streamlit as st
import requests
import pandas as pd
from azure.identity import ClientSecretCredential
from azureml.core import Workspace, Datastore, Dataset
from azure.storage.blob import BlobClient
from io import StringIO
from datetime import datetime
import os

# === 🔐 Authentification via Service Principal ===
tenant_id = os.environ.get("AZURE_TENANT_ID")
client_id = os.environ.get("AZURE_CLIENT_ID")
client_secret = os.environ.get("AZURE_SP_PASSWORD")

if not all([tenant_id, client_id, client_secret]):
    raise ValueError("Les variables d'environnement d'authentification ne sont pas définies.")

credential = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)

# === Connexion à Azure ML ===
ws = Workspace(
    subscription_id="c871724e-63cc-4605-a668-5a6a1b5a925b",
    resource_group="rg_nlp_ara_05",
    workspace_name="housing_workspace",
    auth=credential
)

datastore = Datastore.get(ws, "housing_datastore")
print(f"🔗 Connexion au datastore '{datastore.name}' réussie.")

# === Configuration API & Azure Blob ===
api_url = "https://housingapp2-h9e3hxbwhzahb5cb.francecentral-01.azurewebsites.net/predict"
connection_string = os.environ.get("AZURE_SECRET")

if connection_string is None:
    raise ValueError("Le secret AZURE_SECRET n'a pas été trouvé dans les variables d'environnement.")

container_name = datastore.container_name
blob_path = "data/inference_data.csv"

st.title('Prédiction du prix des appartements')

median_income = st.number_input("Median Income", min_value=0.0, value=3.5)
latitude = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=34.0)
longitude = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=-118.0)

password = st.text_input("Mot de passe", type="password")
valid_password = "california"

# === Chargement ou création du DataFrame d'inférence ===
try:
    dataset = Dataset.Tabular.from_delimited_files(path=(datastore, blob_path))
    print("✅ Dataset d'inférence trouvé sur Azure ML.")
    data_inference = dataset.to_pandas_dataframe()
except Exception as e:
    print("❌ Dataset d'inférence non trouvé, création d'un nouveau DataFrame.")
    data_inference = pd.DataFrame(columns=["median_income", "latitude", "longitude", "prediction", "local_hour"])

# === Blob client pour upload ===
blob_client = BlobClient.from_connection_string(
    conn_str=connection_string,
    container_name=container_name,
    blob_name=blob_path
)

# === Interaction utilisateur ===
if st.button('Obtenir la prédiction'):
    if not password:
        st.error("Veuillez entrer le mot de passe pour continuer.")
    elif password != valid_password:
        st.error("Mot de passe incorrect. Veuillez réessayer.")
    else:
        # Requête vers l'API
        data = {"features": [longitude, latitude, median_income]}
        response = requests.post(api_url, json=data)

        if response.status_code == 200:
            prediction = response.json()
            prix_pred = prediction['prediction'][0]
            st.write(f"Le prix prédit pour cet appartement est : ${prix_pred:,.2f}")

            # === 🔄 Ajout d'une ligne au DataFrame ===
            nouvelle_ligne = {
                "longitude": longitude,
                "latitude": latitude,
                "median_income": median_income,
                "local_hour": pd.Timestamp.now(),
                "prediction": prix_pred
            }
            data_inference = pd.concat([data_inference, pd.DataFrame([nouvelle_ligne])], ignore_index=True)

            # Upload vers Azure Blob Storage
            csv_buffer = StringIO()
            data_inference.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)

            blob_client.upload_blob(csv_buffer.getvalue(), overwrite=True)
            st.success("✅ Données d'inférence mises à jour sur Azure Blob Storage.")
        else:
            st.error(f"Erreur de prédiction, code : {response.status_code}.")
