# https://www.linkedin.com/jobs/search?keywords=Developer&location=%C5%81%C3%B3d%C5%BA%2C%20Woj.%20%C5%81%C3%B3dzkie%2C%20Polska&distance=25
import json
import os
import re
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from databases import Database
import requests
import csv
from bs4 import BeautifulSoup, Comment
from playwright.sync_api import sync_playwright
import langid

from JobOffer import JobOffer
from OfferAnalyze import analyzeOfferDetails


def createFileAndAddHeaders(filename):
    # headers to CSV
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        headers = ['URL']
        writer.writerow(headers)


def scrapeOfferDetails(url, date):
    response = fetch_with_retries(url, retries=5, delay=5)
    if not response:
        print(f"Skipping URL {url} due to repeated failures.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    offerTitle = soup.find("h1", {"class", "top-card-layout__title"}).text.strip()
    offerOrganization = soup.find("a", {"class", "topcard__org-name-link"})
    offerOrganizationURL = offerOrganization["href"].split('?')[0]
    offerOrganization = offerOrganization.text.strip()
    offerLocation = soup.find("span", {"class", "topcard__flavor topcard__flavor--bullet"}).text.strip()
    offerDescription = soup.find("div", {"class", "show-more-less-html__markup"}).get_text(separator="\n").strip()
    offerLanguage, languageConfidence = langid.classify(offerDescription)


    # get offer id from url "-127173516765732"
    match = re.search(r'-(\d+)$', url)
    offer_id = 0
    if match:
        offer_id = match.group(1)  # ID oferty to dopasowana grupa
        print(f"ID oferty: {offer_id}")



    print("=======================")
    print(offerLanguage)
    print(url)
    print(offerTitle)
    print(offerOrganization)
    #print(offerDescription)
    offerJobLevel = soup.find("span", {"class", "description__job-criteria-text"}).text.strip()



    analyzed_details = analyzeOfferDetails(offerLanguage, offerDescription, offerTitle)
    requirements = analyzed_details["requirements"]
    detected_technologies = analyzed_details["detected_technologies"]

    #get apply url hidden in comment
    code_element_ApplyUrl = soup.find('code', {'id': 'applyUrl'})
    offerApplyUrl = url
    if code_element_ApplyUrl:
        comment = code_element_ApplyUrl.find(string=lambda string: isinstance(string, Comment))
        if comment:
            # remove brackets from comment
            offerApplyUrl = comment.strip().strip('"')
            print(f"Extracted URL: {offerApplyUrl}")
        else:
            print("No comment found in the <code> element.")
    else:
        print("No <code> element found with id 'applyUrl'.")


    # Tworzenie obiektu JobOffer
    job_offer = JobOffer(
        url=url,
        date=date,
        title=offerTitle,
        organization=offerOrganization,
        organization_url=offerOrganizationURL,
        location=offerLocation,
        description=offerDescription,
        language=offerLanguage,
        job_level=offerJobLevel,
        apply_url=offerApplyUrl,
        web_id=offer_id,
        requirements=requirements,
        detected_technologies=detected_technologies
    )
    # Debugging: Wyświetlenie informacji o ofercie
    print(f"Parsed JobOffer: {job_offer}")

    return job_offer


def scrapeNumberOfOffers(
        url="https://www.linkedin.com/jobs/search?keywords=Developer&location=%C5%81%C3%B3d%C5%BA%2C%20Woj.%20%C5%81%C3%B3dzkie%2C%20Polska&distance=25"):
    # get number of total pages
    print("url scrapeNumberOfOffers " + url)
    response = fetch_with_retries(url, retries=5, delay=5)
    if not response:
        print(f"Skipping URL {url} due to repeated failures.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    number_of_offers = soup.find("span", {"class", "results-context-header__job-count"}) \
        .text.strip()
    print("Liczba ofert: " + number_of_offers)
    return number_of_offers



def scrapeOffersList(url):
    # get number of total pages
    response = fetch_with_retries(url, retries=5, delay=5)
    if not response:
        print(f"Skipping URL {url} due to repeated failures.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    # Znajdź wszystkie elementy ofert pracy
    offer_cards = soup.find_all('div', {'class': 'base-card'})

    offers = []

    for card in offer_cards:
        # Wyciągnięcie URL oferty
        link_element = card.find('a', {'class': 'base-card__full-link'})
        offer_url = link_element['href'] if link_element else None

        # Wyciągnięcie daty publikacji
        time_element = card.find('time', {'class': 'job-search-card__listdate'})
        offer_date = time_element['datetime'] if time_element else None

        if offer_url:
            offers.append({
                'url': offer_url,
                'date': offer_date
            })

    return offers


def scrapeOffersWithPagination(base_url, numberOfOffers, repeat=0):
    offers = set()  # Zestaw przechowujący unikalne oferty
    runTimes = 0

    while (runTimes <= repeat):
        runTimes += 1
        start = 0
        offers_in_request = 0  # Liczba ofert na stronę (zwykle 10-25 na LinkedIn)

        while (
                (start + offers_in_request) < numberOfOffers
                or
                len(offers) < numberOfOffers
        ):

            start = start + offers_in_request
            paginated_url = f"{base_url}&start={start}"

            print(f"Scraping page(start) {start}/{numberOfOffers}")
            offer_list = scrapeOffersList(paginated_url)

            if not offer_list:
                print("No more offers found or reached end of results.")
                break
            offers_in_request = len(offer_list)
            print(f"offers_in_request {offers_in_request}")
            for link in offer_list:
                try:
                    clean_url = link["url"].split('?')[0]
                    date = link.get('date', None)  # Pobranie daty, jeśli istnieje
                    offer_tuple = (clean_url, date)  # Tworzenie krotki

                    if offer_tuple not in offers:
                        offers.add(offer_tuple)
                    else:
                        print(f"Duplicate offer found: {clean_url}")
                except KeyError:
                    print("Skipping a link without 'url'")
            print(f"Total unique offers scraped: {len(offers)}")

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






searchKeyword = "Developer"
location = "%C5%81%C3%B3d%C5%BA%2C%20Woj.%20%C5%81%C3%B3dzkie%2C%20Polska"
distance = 25

urlForNumberOfOffers = f"https://www.linkedin.com/jobs/search?keywords={searchKeyword}&location={location}&distance={distance}"
url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={searchKeyword}&location={location}"
# scrapeOffersList(url)

numberOfOffers = int(scrapeNumberOfOffers(urlForNumberOfOffers))
if (numberOfOffers):
    offers = scrapeOffersWithPagination(url, numberOfOffers, repeat=0)
    for index, offer in enumerate(offers):
        scrapeOfferDetails(offer[0], offer[1])
