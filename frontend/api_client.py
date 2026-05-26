import requests

API_URL = "http://127.0.0.1:8000/query"


def ask_agent(question: str):

    payload = {
        "question": question
    }

    response = requests.post(API_URL, json=payload)

    if response.status_code != 200:
        return {
            "error": f"API Error: {response.status_code}"
        }

    return response.json()