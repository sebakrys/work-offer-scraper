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


linkedin_joblvl_dictionary = {
    "Początkujący" : "Junior",

    "Kadra średniego szczebla" : "Mid",

    "Specjalista" : "Senior",
}

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
        #print(f"ID oferty: {offer_id}")



    #print("=======================")
    #print(offerLanguage)
    #print(url)
    #print(offerTitle)
    #print(offerOrganization)
    #print(offerDescription)
    offerJobLevel = [
        linkedin_joblvl_dictionary.get(
            soup.find("span", {"class", "description__job-criteria-text"}).text.strip(),
            soup.find("span", {"class", "description__job-criteria-text"}).text.strip())
    ]

    #TODO add employmentType (rodzaj zatrudnienia, np. Umowa o pracę, B2B) [Dotyczy wszytskich stron]
    # TODO add workSchedules (Etat, pełny, niepełny) [Dotyczy wszytskich stron]
    # TODO add workModes (Hybrydowo, zdalnie, stacjonarnie) [Dotyczy wszytskich stron]



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
            #print(f"Extracted URL: {offerApplyUrl}")
        else:
            #print("No comment found in the <code> element.")
            pass
    else:
        #print("No <code> element found with id 'applyUrl'.")
        pass


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
    #print(f"Parsed JobOffer: {job_offer}")

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

            print(f"Scraping page(start) {start}/{numberOfOffers}, runTime:{runTimes}")
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
                        #print(f"Duplicate offer found: {clean_url}")
                        pass
                except KeyError:
                    print("Skipping a link without 'url'")
            print(f"Total unique offers scraped: {len(offers)}")

    print(f"Total unique offers scraped: {len(offers)}")
    return offers




searchKeyword = "Developer"
location = "%C5%81%C3%B3d%C5%BA%2C%20Woj.%20%C5%81%C3%B3dzkie%2C%20Polska"
distance = 25 # in miles

urlForNumberOfOffers = f"https://www.linkedin.com/jobs/search?keywords={searchKeyword}&location={location}&distance={distance}"
url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={searchKeyword}&location={location}"
# scrapeOffersList(url)


def run_LinkedIn_scraper():
    numberOfOffers = int(scrapeNumberOfOffers(urlForNumberOfOffers))
    if (numberOfOffers):
        offers = scrapeOffersWithPagination(url, numberOfOffers, repeat=0)
        for index, offer in enumerate(offers):
            job_offer = scrapeOfferDetails(offer[0], offer[1])
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
                save_job_offer_to_db(job_offer, "LinkedIn")