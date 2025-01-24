# https://www.linkedin.com/jobs/search?keywords=Developer&location=%C5%81%C3%B3d%C5%BA%2C%20Woj.%20%C5%81%C3%B3dzkie%2C%20Polska&distance=25
import json
import math
import os
import re
import time
from datetime import datetime, timedelta
from urllib.parse import quote

from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, Date, ARRAY, JSON
from databases import Database
import requests
import csv
from bs4 import BeautifulSoup, Comment
from playwright.sync_api import sync_playwright
import langid

from JobOffer import JobOffer

from OfferAnalyze import analyzeOfferDetails, filterJobOffer, detectSkillDeficiencies, \
    extract_experience_years_with_context_nlp, \
    extract_experience_years_with_openai, detectExperienceYears, generateSkillsSectionForCV, find_path_to_key, \
    remove_diacritics

from database import save_job_offer_to_db, checkIfOfferExistsInDB
from scraper.shared import all_tech
from web import fetch_with_retries

bulldxgjxb_joblvl_dictionary = {
    "intern": "1_trainee",
    "junior": "3_Junior",
    "medium": "5_Mid",
    "senior": "7_Senior"
}

bulldxgjxb_employmentType_dictionary = {
    "umowa o pracę": "1_UoP",
    "contract of employment": "1_UoP",

    "kontrakt B2B": "2_B2B",
    "B2B contract": "2_B2B",

    "umowa o dzieło": "3_Umowa_o_dzielo",
    "umowa o staż / praktyki": "4_Internship",
    "umowa zlecenie": "5_Contract",
    "umowa agencyjna": "8_agency_agreement",
    "umowa o pracę tymczasową": "9_praca_tymczasowa"
}

bulldxgjxb_WorkSchedules_dictionary = {
    "full_time": "1_Full-time",
    "part_time": "2_Part-time",
    "freelance": "5_Freelance"

}

bulldxgjxb_WorkModes_dictionary = {
    "praca stacjonarna": "1_Full-office",

    "hybrid work": "2_Hybrid",
    "praca hybrydowa": "2_Hybrid",

    "home office work": "3_Home-office",
    "praca zdalna": "3_Home-office",

    "praca mobilna": "4_Mobile"

}


def scrapeOfferDetails(jobOffer):
    response = fetch_with_retries(jobOffer.url, retries=5, delay=5)
    if not response:
        print(f"(BullDxgJxb):Skipping URL {jobOffer.url} due to repeated failures.")
        return
    print(f"(BullDxgJxb):{jobOffer.url}")
    soup = BeautifulSoup(response.text, 'html.parser')

    """
                    date=None,
                    organization_url=None,
                    description=None,
                    language=None,
                    apply_url=None,
                    web_id=slug,
                    requirements=None,
                    detected_technologies=None,
    """
    script_element = soup.find('script', {'id': '__NEXT_DATA__'})
    if script_element:
        json_content = json.loads(json.loads(script_element.string.strip())["props"]["pageProps"]["metaData"]["jsonLd"])
        # date
        date = json_content["datePosted"]
        #organization_url
        organization_url = json_content["hiringOrganization"]['@id']
        #description
        offer_description = json_content["description"]
        # language
        offerLanguage, languageConfidence = langid.classify(offer_description)
        #apply_url TODO nie potrafie wyciągnąc URL
        apply_url = jobOffer.url
        #web_id
        #print(jobOffer.web_id)
        match = re.search(r'^(\d+)-', jobOffer.web_id)
        offer_id = 0
        if match:
            offer_id = match.group(1)  # ID oferty to dopasowana grupa
            #print(f"ID oferty: {offer_id}")

        analyzed_details = analyzeOfferDetails(offerLanguage, offer_description, jobOffer.title)
        requirements = analyzed_details["requirements"]
        detected_technologies = analyzed_details["detected_technologies"]

        jobOffer.date = date
        jobOffer.organization_url = organization_url
        jobOffer.description = offer_description
        jobOffer.language = offerLanguage
        jobOffer.apply_url = apply_url
        jobOffer.web_id = offer_id
        jobOffer.requirements = requirements
        jobOffer.detected_technologies = detected_technologies


    return jobOffer


def scrapeNumberOfOffers(
        url="https://bulldogjob.pl/companies/jobs/s/city,%C5%81%C3%B3d%C5%BA/experienceLevel,intern,junior,medium"):
    # get number of total pages
    print("(BullDxgJxb):url scrapeNumberOfOffers " + url)
    response = fetch_with_retries(url, retries=5, delay=5)
    if not response:
        print(f"(BullDxgJxb):Skipping URL {url} due to repeated failures.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    script_element = soup.find('script', {'id': '__NEXT_DATA__'})
    number_of_offers = 0
    max_page = 0
    if script_element:
        # Pobierz zawartość jako tekst
        script_content = script_element.string.strip()
        number_of_offers = json.loads(script_content)["props"]["pageProps"]["totalCount"]
        per_page = json.loads(script_content)["props"]["pageProps"]["slugState"]["perPage"]
        max_page = math.ceil(number_of_offers / per_page)
    print("(BullDxgJxb):Liczba ofert: " + str(number_of_offers))
    print(f"(BullDxgJxb):Liczba stron: {max_page}")
    return number_of_offers, int(max_page)


def scrapeOffersList(url, location = "Łódź", baseOfferDetailsURL = "https://bulldogjob.pl/companies/jobs/"):
    # get number of total pages
    response = fetch_with_retries(url, retries=5, delay=5)
    if not response:
        print(f"(BullDxgJxb):Skipping URL {url} due to repeated failures.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    script_element = soup.find('script', {'id': '__NEXT_DATA__'})

    offers = []

    if script_element:
        # Pobierz zawartość jako tekst
        json_content = json.loads(script_element.string.strip())



        for job in json_content["props"]["pageProps"]["jobs"]:  # normal job offers
            if (job.get("__typename") and job["__typename"] == "Job"):
                slug = job["id"]

                if (job["environment"]["remotePossible"] > 0):  # okreslanie na podstawie liczby dni w tygodniu zdalnie
                    if (job["environment"]["remotePossible"] == 100):
                        workModes = "3_Home-office"
                    else:
                        workModes = "2_Hybrid"
                else:
                    workModes = ["1_Full-office"]

                offerLocation = ""
                cities = [city.strip() for city in job["city"].split(',')]
                #print(f'cities: {cities}')
                #print(f'remove_diacritics(location): {remove_diacritics(location)}')
                for city in cities:
                    if(city == remove_diacritics(location) or city == location): offerLocation = city


                job_level = bulldxgjxb_joblvl_dictionary.get(job["experienceLevel"], job["experienceLevel"])
                workSchedule = bulldxgjxb_WorkSchedules_dictionary.get(job["employmentType"], job["employmentType"])


                employmentTypes = []
                contractB2B = job["contractB2b"]
                if(contractB2B): employmentTypes.append("2_B2B")
                contractEmployment = job["contractEmployment"]
                if (contractEmployment): employmentTypes.append("1_UoP")
                contractOther = job["contractOther"]
                if(contractOther): employmentTypes.append("7_Other/Any")





                offers.append(JobOffer(
                    url=baseOfferDetailsURL + slug,#
                    title=job["position"],#
                    organization=job["company"]["name"],#
                    location=offerLocation,#
                    job_level=[job_level],#
                    employmentType=employmentTypes,#
                    workSchedules=[workSchedule],#
                    workModes=workModes,#
                    date=None,
                    organization_url=None,
                    description=None,
                    language=None,
                    apply_url=None,
                    web_id=slug,
                    requirements=None,
                    detected_technologies=None,
                ))

    return offers


def scrapeOffersWithPagination(base_url, numberOfOffers, max_page=1, repeat=0, location="Łódź"):
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

            paginated_url = f"{base_url}/page,{page}"

            print(f"(BullDxgJxb): Scraping page: {page}/{max_page}, runTime:{runTimes}")
            offer_list = scrapeOffersList(paginated_url, location=location)

            if not offer_list:
                print("(BullDxgJxb):No more offers found or reached end of results.")
                break
            offers_in_request = len(offer_list)
            #print(f"offers_in_request {offers_in_request}")
            for single_offer in offer_list:
                try:
                    if single_offer not in offers:
                        offers.add(single_offer)
                    else:
                        #print(f"Duplicate offer found: {single_offer.url}")
                        pass
                except KeyError:
                    print("(BullDxgJxb):Skipping a link without 'url'")
            #print(f"Total unique offers scraped: {len(offers)}")
            page+=1

    print(f"(BullDxgJxb):Total unique offers scraped: {len(offers)}")
    return offers


location = "Łódź"
experienceLevel = "intern,junior,medium"

urlForNumberOfOffers = f"https://bulldogjob.pl/companies/jobs/s/city,{quote(location)}/experienceLevel,{experienceLevel}"
url = f"https://bulldogjob.pl/companies/jobs/s/city,{quote(location)}/experienceLevel,{experienceLevel}"  # /page,2


def run_BullDxgJxb_scraper(updateInCaseOfExistingInDB=True, updateOpenAIApiPart=False):
    start_time = time.monotonic()
    numberOfOffers, max_page = scrapeNumberOfOffers(urlForNumberOfOffers)
    if (numberOfOffers):
        offers = scrapeOffersWithPagination(url, numberOfOffers, max_page, repeat=1, location = location)
        for index, offer in enumerate(offers):
            job_offer = scrapeOfferDetails(offer)
            if (filterJobOffer(job_offer)):
                offerExists = checkIfOfferExistsInDB(web_id=job_offer.web_id, url=job_offer.url)
                if ((not offerExists.exists) or updateInCaseOfExistingInDB):
                    #print("======================")
                    job_offer.skill_deficiencies = detectSkillDeficiencies(job_offer)
                    if (updateOpenAIApiPart or (not offerExists.exists)):
                        job_offer.experience_years = detectExperienceYears(job_offer)
                        #print(job_offer.experience_years)
                        job_offer.skills_for_cv = generateSkillsSectionForCV(job_offer)
                    #print(job_offer.url)
                    job_offer.skill_percentage = 1.0 - (float(len(job_offer.skill_deficiencies)) / float(
                        sum(len(value) for value in job_offer.detected_technologies.values())))
                    print(f"(BullDxgJxb):{job_offer.skill_percentage}")
                    #print(f"LEN: skill_deficiencies/detected_technologies: {len(job_offer.skill_deficiencies)}/{sum(len(value) for value in job_offer.detected_technologies.values())}")
                    #print(f"skill_deficiencies: {(job_offer.skill_deficiencies)}, detected_technologies: {(job_offer.detected_technologies)}")
                    save_job_offer_to_db(job_offer, "BullDogJobs.pl", updateInCaseOfExistingInDB=updateInCaseOfExistingInDB,
                                         updateOpenAIApiPart=updateOpenAIApiPart)
    end_time = time.monotonic()
    print(f"(BullDxgJxb): total time: {timedelta(seconds=end_time - start_time)}")