# https://www.linkedin.com/jobs/search?keywords=Developer&location=%C5%81%C3%B3d%C5%BA%2C%20Woj.%20%C5%81%C3%B3dzkie%2C%20Polska&distance=25
import json
import os
import re
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, Date, ARRAY, JSON
from databases import Database
import requests
import csv
from bs4 import BeautifulSoup, Comment
from playwright.sync_api import sync_playwright
import langid

from JobOffer import JobOffer
from OfferAnalyze import analyzeOfferDetails, filterJobOffer, detectSkillDeficiencies
from database import save_job_offer_to_db
from web import fetch_with_retries

pracujpl_joblvl_dictionary = {
    "trainee" : "trainee",
    "praktykant / stażysta" : "trainee",

    "junior specialist (Junior)" : "Junior",
    "młodszy specjalista (Junior)" : "Junior",

    "specjalista (Mid / Regular)" : "Mid",
    "specialist (Mid / Regular)" : "Mid",

    "starszy specjalista (Senior)" : "Senior",
    "senior specialist (Senior)" : "Senior"
}


def scrapeOfferDetails(url, date, company_url):
    response = fetch_with_retries(url, retries=5, delay=5)
    if not response:
        print(f"Skipping URL {url} due to repeated failures.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    offerTitle = soup.find('h1', {'data-scroll-id': 'job-title'}).text.strip()
    offerOrganization = soup.find("h2", {"data-scroll-id": "employer-name"}).contents[0].strip()
    offerOrganizationURL = company_url

    script_element = soup.find('script', {'id': '__NEXT_DATA__'})
    offerLocation = json.loads(script_element.string.strip())["props"]["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]["attributes"]["workplaces"][0]["displayAddress"]
    print(url)

    requirements = soup.find("section", {"data-test": "section-requirements"})
    if(requirements):
        requirements_part_of_description = requirements.get_text(separator="\n").strip()
        requirements = requirements.get_text(separator="\n").splitlines()
    else:
        requirements_part_of_description=""
        requirements=[]

    #print("requirements")
    #print(requirements)





    about_project_page_element = soup.find("section", {"data-test": "text-about-project"})
    about_project = ""
    if(about_project_page_element):
        about_project = about_project_page_element.get_text(separator="\n").strip()

    offerDescription = f'{about_project} {requirements_part_of_description}'

    #print(offerDescription)
    offerLanguage, languageConfidence = langid.classify(offerDescription)


    # get offer id from url "-127173516765732"
    match = re.search(r',(\d+)$', url)
    offer_id = 0
    if match:
        offer_id = match.group(1)  # ID oferty to dopasowana grupa
        print(f"ID oferty: {offer_id}")



    #print("=======================")
    print(offerLanguage)
    print(url)
    #print(offerTitle)
    #print(offerOrganization)
    #print(offerDescription)

    levels = []
    for lvl in json.loads(script_element.string.strip())["props"]["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]["attributes"]["employment"]["positionLevels"]:
        original_level = lvl["name"]
        mapped_level = pracujpl_joblvl_dictionary.get(original_level, original_level)
        levels.append(mapped_level)
    #offerJobLevel = ", ".join(levels)
    print(levels)

    #print(json.loads(script_element.string.strip())["props"]["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]["attributes"]["employment"]["positionLevels"])
    #print(find_path_to_key(json.loads(script_element.string.strip()), "positionLevels"))





    detected_technologies_direct_from_site_expected = [span.get_text(strip=True) for span in soup.find_all('span', {'data-test': 'item-technologies-expected'})]
    print(detected_technologies_direct_from_site_expected)#TODO mozna wykorzytsac do zrobienia kompleksowej(globalnej) listy technologi
    detected_technologies_direct_from_site_optional = [span.get_text(strip=True) for span in soup.find_all('span', {'data-test': 'item-technologies-optional'})]
    #print(detected_technologies_direct_from_site_optional)#TODO mozna wykorzytsac do zrobienia kompleksowej(globalnej) listy technologi

    analyzed_details = analyzeOfferDetails(offerLanguage, offerDescription, offerTitle, detected_technologies_direct_from_site_expected)
    detected_technologies = analyzed_details["detected_technologies"]

    #get apply url hidden in comment
    element_ApplyUrl = soup.find('a', {'data-test': 'anchor-apply'})
    offerApplyUrl = element_ApplyUrl['href'].split('?')[0] if element_ApplyUrl else ""



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
        job_level=levels,
        apply_url=offerApplyUrl,
        web_id=offer_id,
        requirements=requirements,
        detected_technologies=detected_technologies
    )
    # Debugging: Wyświetlenie informacji o ofercie
    #print(f"Parsed JobOffer: {job_offer}")

    return job_offer


def scrapeNumberOfOffers(
        url="https://www.pracuj.pl/praca/developer;kw/lodz;wp?rd=50&et=1%2C17%2C4"):
    # get number of total pages
    print("url scrapeNumberOfOffers " + url)
    response = fetch_with_retries(url, retries=5, delay=5)
    if not response:
        print(f"Skipping URL {url} due to repeated failures.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    script_element = soup.find('script', {'id': '__NEXT_DATA__'})
    number_of_offers = 0
    if script_element:
        # Pobierz zawartość jako tekst
        script_content = script_element.string.strip()
        number_of_offers =json.loads(script_content)["props"]["pageProps"]["data"]["jobOffers"]["offersTotalCount"]
    print("Liczba ofert: " + str(number_of_offers))
    max_page = soup.find('span', {'data-test': 'top-pagination-max-page-number'}).text.strip()
    print(f"Liczba stron: {max_page}")
    return number_of_offers, int(max_page)


def find_path_to_key(data, target_key, target_value=None, current_path=""):
    """
    Znajduje ścieżkę do danego klucza (i opcjonalnie wartości) w drzewiastym JSON-ie.

    :param data: Obiekt JSON (słownik lub lista).
    :param target_key: Klucz, którego szukamy.
    :param target_value: Wartość, którą opcjonalnie chcemy dopasować.
    :param current_path: Aktualna ścieżka w przeszukiwanym JSON-ie.
    :return: Ścieżka do klucza lub None.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f"{current_path}.{key}" if current_path else key
            if key == target_key:
                if target_value is None or value == target_value:
                    return new_path
            # Rekursja dla zagnieżdżonego słownika
            result = find_path_to_key(value, target_key, target_value, new_path)
            if result:
                return result
    elif isinstance(data, list):
        for index, item in enumerate(data):
            new_path = f"{current_path}[{index}]"
            # Rekursja dla każdego elementu listy
            result = find_path_to_key(item, target_key, target_value, new_path)
            if result:
                return result
    return None



def scrapeOffersList(url):
    # get number of total pages
    response = fetch_with_retries(url, retries=5, delay=5)
    if not response:
        print(f"Skipping URL {url} due to repeated failures.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')





    script_element = soup.find('script', {'id': '__NEXT_DATA__'})

    offers = []

    if script_element:
        # Pobierz zawartość jako tekst
        json_content = json.loads(script_element.string.strip())



        for job in json_content["props"]["pageProps"]["data"]["jobOffers"]["groupedOffers"]:# normal job offers
            if job["offers"][0]["offerAbsoluteUri"]:
                offers.append({
                    'url': job["offers"][0]["offerAbsoluteUri"],
                    'date': job["lastPublicated"],
                    'company_url': job["companyProfileAbsoluteUri"]
                })

            print(job["offers"][0]["offerAbsoluteUri"])
            print(job["lastPublicated"])

        for positioned_job in json_content["props"]["pageProps"]["data"]["positionedJobOffers"]["groupedOffers"]:# positioned job offers
            if positioned_job["offers"][0]["offerAbsoluteUri"]:
                offers.append({
                    'url': positioned_job["offers"][0]["offerAbsoluteUri"],
                    'date': positioned_job["lastPublicated"],
                    'company_url': positioned_job["companyProfileAbsoluteUri"]
                })
            print(positioned_job["offers"][0]["offerAbsoluteUri"])
            print(positioned_job["lastPublicated"])

    return offers


def scrapeOffersWithPagination(base_url, numberOfOffers, max_page=1, repeat=0):
    offers = set()  # Zestaw przechowujący unikalne oferty
    runTimes = 0

    while (runTimes <= repeat):
        runTimes += 1
        page = 1

        while (
                page <= max_page
                or
                len(offers) < numberOfOffers
        ):

            paginated_url = f"{base_url}&pn={page}"

            print(f"Scraping page: {page}/{max_page}, runTime:{runTimes}")
            offer_list = scrapeOffersList(paginated_url)

            if not offer_list:
                print("No more offers found or reached end of results.")
                break
            offers_in_request = len(offer_list)
            print(f"offers_in_request {offers_in_request}")
            for single_offer in offer_list:
                try:
                    offer_tuple = (single_offer["url"], single_offer["date"], single_offer["company_url"])  # Tworzenie krotki

                    if offer_tuple not in offers:
                        offers.add(offer_tuple)
                    else:
                        print(f"Duplicate offer found: {single_offer['url']}")
                        pass
                except KeyError:
                    print("Skipping a link without 'url'")
            print(f"Total unique offers scraped: {len(offers)}")
            page+=1

    print(f"Total unique offers scraped: {len(offers)}")
    return offers




searchKeyword = "developer"
location = "lodz"
distance = 50

urlForNumberOfOffers = f"https://www.pracuj.pl/praca/{searchKeyword};kw/{location};wp?rd={distance}&et=1%2C17%2C4"#&et=1%2C17%2C4 - for trainee/Junior/Mid
url = f"https://www.pracuj.pl/praca/{searchKeyword};kw/{location};wp?rd={distance}&et=1%2C17%2C4"



def run_PracujPL_scraper():
    numberOfOffers, max_page = scrapeNumberOfOffers(urlForNumberOfOffers)
    if (numberOfOffers):
        offers = scrapeOffersWithPagination(url, numberOfOffers, max_page, repeat=0)
        for index, offer in enumerate(offers):
            job_offer = scrapeOfferDetails(offer[0], offer[1], offer[2])
            if (filterJobOffer(job_offer)):
                print("======================")
                job_offer.skill_deficiencies = detectSkillDeficiencies(job_offer)
                print(job_offer.url)
                job_offer.skill_percentage = 1.0 - (float(len(job_offer.skill_deficiencies)) / float(
                    sum(len(value) for value in job_offer.detected_technologies.values())))
                print(job_offer.skill_percentage)
                print(
                    f"LEN: skill_deficiencies/detected_technologies: {len(job_offer.skill_deficiencies)}/{sum(len(value) for value in job_offer.detected_technologies.values())}")
                print(
                    f"skill_deficiencies: {(job_offer.skill_deficiencies)}, detected_technologies: {(job_offer.detected_technologies)}")
                save_job_offer_to_db(job_offer, "Pracuj.pl")