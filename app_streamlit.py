import streamlit as st
import requests

# URL de l'API FastAPI
api_url = "http://127.0.0.1:8000/predict"

# Titre de l'application
st.title('Prédiction du prix des appartements')

# Entrée des trois features
median_income = st.number_input("Median Income", min_value=0.0, value=3.5)
latitude = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=34.0)
longitude = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=-118.0)

# Entrée du mot de passe
password = st.text_input("Mot de passe", type="password")

# Si tu veux un mot de passe simple pour tester
valid_password = "california"  # Mot de passe à vérifier

# Bouton pour obtenir la prédiction
if st.button('Obtenir la prédiction'):
    if not password:
        st.error("Veuillez entrer le mot de passe pour continuer.")
    elif password != valid_password:
        st.error("Mot de passe incorrect. Veuillez réessayer.")
    else:
        # Si le mot de passe est correct, on fait la prédiction
        data = {
            "features": [median_income, latitude, longitude]
        }

        # Faire une requête POST à l'API pour obtenir la prédiction
        prediction_response = requests.post(api_url, json=data)

        # Afficher le résultat
        if prediction_response.status_code == 200:
            prediction = prediction_response.json()
            st.write(f"Le prix prédit pour cet appartement est : ${prediction['prediction'][0]:,.2f}")
        else:
            st.error(f"Erreur de prédiction, code d'erreur : {prediction_response.status_code}. Vérifiez que l'API est en cours d'exécution.")
