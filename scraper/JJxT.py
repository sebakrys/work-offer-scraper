# https://www.linkedin.com/jobs/search?keywords=Developer&location=%C5%81%C3%B3d%C5%BA%2C%20Woj.%20%C5%81%C3%B3dzkie%2C%20Polska&distance=25
import hashlib
import json
import os
import re
import time
from datetime import datetime, timedelta

from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, Date, ARRAY, JSON
from databases import Database
import requests
import csv
from bs4 import BeautifulSoup, Comment
from playwright.sync_api import sync_playwright
import langid
from urllib.parse import quote


from JobOffer import JobOffer

from OfferAnalyze import analyzeOfferDetails, filterJobOffer, detectSkillDeficiencies, \
    extract_experience_years_with_context_nlp, \
    extract_experience_years_with_openai, detectExperienceYears, generateSkillsSectionForCV, generate_web_id_from_text

from database import save_job_offer_to_db, checkIfOfferExistsInDB
from scraper.shared import all_tech

from web import fetch_with_retries

jjit_joblvl_dictionary = {
    "trainee" : "1_trainee",
    "junior" : "3_Junior",
    "mid" : "5_Mid",
    "senior" : "7_Senior"
}

jjit_employmentType_dictionary = {
    "permanent":"1_UoP",
    "b2b": "2_B2B",
    "internship":"4_Internship",
    "any": "7_Other/Any"
}



jjit_WorkSchedules_dictionary = {
    "full_time" : "1_Full-time",
    "part_time" : "2_Part-time",

    "internship": "4_Intership",
    "freelance": "5_Freelance",
    "Undetermined": "9_Undetermined"


}

jjit_WorkModes_dictionary = {
    "office" : "1_Full-office",
    "hybrid" : "2_Hybrid",
    "remote": "3_Home-office"


}


def scrapeOfferDetails(jobOffer):
    response = fetch_with_retries(jobOffer.url, retries=5, delay=5)
    if not response:
        print(f"(JJxT): Skipping URL {url} due to repeated failures.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    """
                description=None,
                language=None,
                apply_url=None,
                web_id=None,
                requirements=job["requiredSkills"],  # TODO zaktualizować na podstawie details
                detected_technologies=None,
    """
    print(f"(JJxT): {jobOffer.url}")

    #description
    description = soup.find('div', {"class": "MuiBox-root css-tbycqp"}).get_text(separator="\n").strip()
    #language
    offerLanguage, languageConfidence = langid.classify(description)
    #apply url
    script_elements = soup.find_all('script')
    apply_url = None
    for script in script_elements:
        if script.string and "applyUrl" in script.string:
            try:
                # Odczytanie JSON-a z tekstu (usunięcie niepotrzebnych elementów)
                pseudo_json_content = script.string.split("[", 1)[1].rsplit("]", 1)[0].replace('\\"', '"').replace('\\n"', "").replace('1,"5:', "")
                #print(pseudo_json_content)
                match = re.search(r'"applyUrl":"([a-zA-Z][a-zA-Z0-9+.-]*:\/\/[^\s"]+)"', pseudo_json_content)
                if match:
                    apply_url = match.group(1)  # ID oferty to dopasowana grupa
                    #print(f"apply_url: {apply_url}")
                break  # Zakończ, jeśli znalazłeś URL
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                print("(JJxT): Błąd podczas przetwarzania JSON-a:", e)
    if apply_url:
        #print("Apply URL:", apply_url)
        pass
    else:
        #print("Nie znaleziono URL-a w skryptach.")
        apply_url = jobOffer.url #wówczas aplikacja jest poprzez strone oferty
    #web_id - brak jest webid w formie liczby, uzywany jest slug, dlatego zahashuje sluga
    hashed_web_id = generate_web_id_from_text(jobOffer.web_id, 12)
    #print(hashed_web_id)
    #requirements
    analyzed_details = analyzeOfferDetails(offerLanguage, description, jobOffer.title, obtainedTechnologiesList=jobOffer.requirements)
    requirements = analyzed_details["requirements"]
    #detected_technologies
    detected_technologies = analyzed_details["detected_technologies"]

    #print(jobOffer.employmentType)
    #print(jobOffer.workSchedules)
    #print(jobOffer.workModes)


    jobOffer.description = description
    jobOffer.language = offerLanguage
    jobOffer.apply_url = apply_url
    jobOffer.web_id = hashed_web_id
    jobOffer.requirements = requirements
    jobOffer.detected_technologies = detected_technologies

    return jobOffer


def scrapeNumberOfOffers(
        url="https://api.justjoin.it/v2/user-panel/offers/by-cursor?city=%C5%81%C3%B3d%C5%BA&currency=pln&experienceLevels[]=junior&experienceLevels[]=mid&orderBy=DESC&sortBy=published&from=0&itemsCount=1"):
    # get number of total pages
    print("(JJxT): url scrapeNumberOfOffers " + url)
    response = fetch_with_retries(url, retries=5, delay=5)
    if not response:
        print(f"(JJxT): Skipping URL {url} due to repeated failures.")
        return
    #print(response.json()["meta"]["totalItems"])
    number_of_offers = response.json()["count"]
    print(f"(JJxT): number_of_offers: {number_of_offers}")

    return number_of_offers


def scrapeOffersList(url, baseOfferDetailsURL = "https://justjoin.it/job-offer/", location="Łódź"):
    # get number of total pages
    response = fetch_with_retries(url, retries=5, delay=5, headers={"Version": "2"})
    if not response:
        print(f"(JJxT): Skipping URL {url} due to repeated failures.")
        return

    json_content = response.json()

    offers = []

    for job in json_content["data"]:# normal job offers
        if job["slug"]:
            #print(job["slug"])
            slug = job["slug"]
            if(job["multilocation"]):
                #print("Multilocation")#wiele lokacji, wybrac na podstawie zapytania włąściwą lokalizację
                for job_location in job["multilocation"]:
                    if(job_location["city"] == location):
                        #print(job_location)
                        slug = job_location["slug"]

            employmentTypes = []
            for employmentType in job["employmentTypes"]:
                employmentTypes.append(jjit_employmentType_dictionary.get(employmentType["type"], employmentType["type"]))



            offers.append(JobOffer(
                url=baseOfferDetailsURL+slug,
                date=job["publishedAt"],
                title=job["title"],
                organization=job["companyName"],
                organization_url="https://justjoin.it/job-offers/all-locations?keyword="+(job["companyName"].replace(" ", "+")),
                location=location,
                job_level=[jjit_joblvl_dictionary.get(job["experienceLevel"], job["experienceLevel"])],
                employmentType=employmentTypes,
                workSchedules=[jjit_WorkSchedules_dictionary.get(job["workingTime"], job["workingTime"])],
                workModes=[jjit_WorkModes_dictionary.get(job["workplaceType"], job["workplaceType"])],
                description=None,
                language=None,
                apply_url=None,
                web_id=slug,
                requirements=job["requiredSkills"],
                detected_technologies=None,
            ))
            all_tech.update(job["requiredSkills"])#TODO temporary
            #print("All tech:")
            #print(all_tech)
            #print(baseOfferDetailsURL+slug)
            #print(job["title"])

    return offers


def scrapeOffersWithPagination(base_url, numberOfOffers,  repeat=0, singleLoadNumberOfOffers = 10, baseOfferDetailsURL = "https://justjoin.it/job-offer/", location="Łódź"):
    offers = set()  # Zestaw przechowujący unikalne oferty
    runTimes = 0

    while (runTimes <= repeat):
        runTimes += 1
        page = 1

        while (
                len(offers) < numberOfOffers
        ):

            paginated_url = f"{base_url}&page={page}&perPage={singleLoadNumberOfOffers}"

            print(f"(JJxT): Scraping offers: {page*singleLoadNumberOfOffers}/{numberOfOffers}, runTime:{runTimes}")
            offer_list = scrapeOffersList(paginated_url, baseOfferDetailsURL = baseOfferDetailsURL, location=location)

            if not offer_list:
                print("(JJxT): No more offers found or reached end of results.")
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
                    #print("Skipping a link without 'url'")
                    pass
            #print(f"Total unique offers scraped: {len(offers)}")
            page+=1

    print(f"(JJxT): Total unique offers scraped: {len(offers)}")
    return offers




searchKeyword = "developer"

location = "Łódź"

#location_for_API="%C5%81%C3%B3d%C5%BA" #translates into Łódź, to obtain in use quote(location)

experienceLevel = "experienceLevels[]=junior&experienceLevels[]=mid"

urlForNumberOfOffers = f"https://api.justjoin.it/v2/user-panel/offers/count?city={quote(location)}&{experienceLevel}"

url = f"https://api.justjoin.it/v2/user-panel/offers/by-cursor?city={quote(location)}&currency=pln&{experienceLevel}&orderBy=DESC&sortBy=published"

url_v2 = f"https://api.justjoin.it/v2/user-panel/offers?city={quote(location)}&{experienceLevel}&sortBy=published&orderBy=DESC"


baseOfferDetailsURL = "https://justjoin.it/job-offer/"





def run_JJXT_scraper(updateInCaseOfExistingInDB=True, updateOpenAIApiPart=False):
    start_time = time.monotonic()
    numberOfOffers= int(scrapeNumberOfOffers(urlForNumberOfOffers))
    if (numberOfOffers):
        offers = scrapeOffersWithPagination(url_v2, numberOfOffers,  repeat=1, singleLoadNumberOfOffers=10, baseOfferDetailsURL=baseOfferDetailsURL, location=location)
        for index, offer in enumerate(offers):
            job_offer = scrapeOfferDetails(offer)
            if (filterJobOffer(job_offer)):
                offerExists = checkIfOfferExistsInDB(web_id=job_offer.web_id, url=job_offer.url)
                if ((not offerExists.exists) or updateInCaseOfExistingInDB):
                    #print("======================")
                    job_offer.skill_deficiencies = detectSkillDeficiencies(job_offer)
                    if(updateOpenAIApiPart or (not offerExists.exists)):
                        job_offer.experience_years = detectExperienceYears(job_offer)
                        #print(job_offer.experience_years)
                        job_offer.skills_for_cv = generateSkillsSectionForCV(job_offer)
                    #print(job_offer.url)
                    job_offer.skill_percentage = 1.0 - (float(len(job_offer.skill_deficiencies)) / float(
                        sum(len(value) for value in job_offer.detected_technologies.values())))
                    #print(job_offer.skill_percentage)
                    #print(f"LEN: skill_deficiencies/detected_technologies: {len(job_offer.skill_deficiencies)}/{sum(len(value) for value in job_offer.detected_technologies.values())}")
                    #print(f"skill_deficiencies: {(job_offer.skill_deficiencies)}, detected_technologies: {(job_offer.detected_technologies)}")
                    save_job_offer_to_db(job_offer, "JJIT", updateInCaseOfExistingInDB=updateInCaseOfExistingInDB, updateOpenAIApiPart=updateOpenAIApiPart)
    end_time = time.monotonic()
    print(f"(JJxT): total time: {timedelta(seconds=end_time - start_time)}")