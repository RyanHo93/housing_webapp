import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Simulation des variables d'entrée
longitude = -118.0
latitude = 34.0
median_income = 3.5
prediction_mock = {"prediction": [123456.78]}


# Test de l'appel à l'API de prédiction
@patch("requests.post")
def test_prediction_api_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = prediction_mock
    mock_post.return_value = mock_response

    from requests import post
    response = post("https://fakeurl.com", json={"features": [longitude, latitude, median_income]})
    
    assert response.status_code == 200
    assert response.json()["prediction"][0] == 123456.78


# Test de l'insertion MySQL (simulation de la base)
@patch("pymysql.connect")
def test_mysql_insert_success(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Appel simulé de l'insertion
    from pymysql import connect
    conn = connect()
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
            123456.78
        ))
    conn.commit()

    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()
