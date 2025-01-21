import requests
import time

def fetch_with_retries(url, retries=3, delay=2, method="GET", headers=None, data=None):
    """
    Pobiera dane z podanego URL z mechanizmem ponawiania prób w przypadku błędów HTTP.
    :param url: URL do pobrania
    :param retries: Maksymalna liczba prób
    :param delay: Opóźnienie między próbami (w sekundach)
    :param method: Metoda HTTP ("GET" lub "POST")
    :param headers: Nagłówki do dołączenia do żądania
    :param data: Dane do wysłania w przypadku żądania POST
    :return: Odpowiedź HTTP (response) lub None
    """
    for attempt in range(1, retries + 1):
        try:
            if (attempt > 1):
                print(f"Fetching URL: {url} (Attempt {attempt}/{retries})")
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            else:
                print(f"Unsupported method: {method}")
                return None
            response.raise_for_status()  # Wyjątek, jeśli status >= 400
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            if attempt < retries:
                #print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Maximum retries reached. Skipping.")
                return None