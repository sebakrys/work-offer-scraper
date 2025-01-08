# https://www.linkedin.com/jobs/search?keywords=Developer&location=%C5%81%C3%B3d%C5%BA%2C%20Woj.%20%C5%81%C3%B3dzkie%2C%20Polska&distance=25

import os
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from databases import Database
import requests
import csv
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def createFileAndAddHeaders(filename):
    # headers to CSV
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        headers = ['URL']
        writer.writerow(headers)

def scrapeOffersList(url):
    # get number of total pages
    response = fetch_with_retries(url,retries=5, delay=5)
    if not response:
        print(f"Skipping URL {url} due to repeated failures.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    offerLinkList = soup.find_all('a', {'class': 'base-card__full-link'})

    number_of_offers = soup.find("span", {"class", "results-context-header__job-count"})\
        .text.strip()
    print("Liczba ofert: "+number_of_offers)

    for offerLink in offerLinkList:
        print(offerLink["href"])
    print(len(offerLinkList))
    return offerLinkList


def scrapeOffersWithPagination(base_url, max_pages=10):
    offers = set()  # Zestaw przechowujący unikalne oferty
    offers_per_page = 25  # Liczba ofert na stronę (zwykle 25 na LinkedIn)

    for page_num in range(max_pages):
        position = page_num * offers_per_page
        paginated_url = f"{base_url}&position={position}&pageNum={page_num}"

        print(f"Scraping page {page_num + 1}: {paginated_url}")
        offer_links = scrapeOffersList(paginated_url)

        if not offer_links:
            print("No more offers found or reached end of results.")
            break

        for link in offer_links:
            try:
                clean_url = link["href"].split('?')[0]
                if clean_url not in offers:
                    offers.add(clean_url)
                else:
                    print(f"Duplicate offer found: {clean_url}")
            except KeyError:
                print("Skipping a link without 'href'")

    print(f"Total unique offers scraped: {len(offers)}")
    return offers



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
            if(attempt>1):
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



# Ładowanie zmiennych środowiskowych
load_dotenv()

# Konfiguracja bazy danych
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")

database = Database(DATABASE_URL)
metadata = MetaData()

# Definicja tabeli ofert pracy
users_table = Table(
    "work_offers",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String(100), nullable=False),
    Column("url", String(100), unique=False, nullable=False),
    Column("desciption", String(100), nullable=False),
)

url = "https://www.linkedin.com/jobs/search?keywords=Developer&location=%C5%81%C3%B3d%C5%BA%2C%20Woj.%20%C5%81%C3%B3dzkie%2C%20Polska&distance=25"

#scrapeOffersList(url)

offers = scrapeOffersWithPagination(url, max_pages=5)