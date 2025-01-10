import requests
import time

def fetch_with_retries(url, retries=3, delay=2):
    """
    Pobiera dane z podanego URL z mechanizmem ponawiania prób w przypadku błędów HTTP.
    :param url: URL do pobrania
    :param retries: Maksymalna liczba prób
    :param delay: Opóźnienie między próbami (w sekundach)
    :return: Odpowiedź HTTP (response) lub None
    """
    for attempt in range(1, retries + 1):
        try:
            if (attempt > 1):
                print(f"Fetching URL: {url} (Attempt {attempt}/{retries})")
            response = requests.get(url)
            response.raise_for_status()  # Wyjątek, jeśli status >= 400
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            if attempt < retries:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Maximum retries reached. Skipping.")
                return None