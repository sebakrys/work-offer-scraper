# https://www.linkedin.com/jobs/search?keywords=Developer&location=%C5%81%C3%B3d%C5%BA%2C%20Woj.%20%C5%81%C3%B3dzkie%2C%20Polska&distance=25
import datetime
from datetime import datetime
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
from OfferAnalyze import analyzeOfferDetails, filterJobOffer, detectSkillDeficiencies, \
    extract_experience_years_with_context_nlp, extract_experience_years_with_openai, detectExperienceYears, \
    generateSkillsSectionForCV, find_path_to_key, generate_web_id_from_text
from database import save_job_offer_to_db, checkIfOfferExistsInDB
from web import fetch_with_retries


nfj_joblvl_dictionary = {
    "trainee" : "1_trainee",
    "Trainee" : "1_trainee",
    "junior" : "3_Junior",
    "Junior" : "3_Junior",
    "mid" : "5_Mid",
    "Mid" : "5_Mid",
    "senior" : "7_Senior",
    "Senior" : "7_Senior"
}

nfj_employmentType_dictionary = {
    "permanent":"1_UoP",
    "b2b": "2_B2B",
    "zlecenie": "5_Contract",


    "internship":"4_Internship",
    "any": "7_Other/Any"
}



nfj_WorkSchedules_dictionary = {
    "full_time" : "1_Full-time",
    "part_time" : "2_Part-time",

    "internship": "4_Intership",
    "freelance": "5_Freelance",
    "Undetermined": "9_Undetermined"


}

nfj_WorkModes_dictionary = {
    "office" : "1_Full-office",
    "hybrid" : "2_Hybrid",
    "remote": "3_Home-office"


}

def scrapeOfferDetails(jobOffer):
    response = fetch_with_retries(jobOffer.url, retries=5, delay=5)
    if not response:
        print(f"Skipping URL {url} due to repeated failures.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')


    response_API = fetch_with_retries(f"https://nofluffjobs.com/api/posting/{jobOffer.web_id}", retries=5, delay=5)
    if not response_API:
        print(f"Skipping URL {url} due to repeated failures.")
        return
    response_JSON = response_API.json()


    """
                organization_url=None,
                workSchedules=None,
                workModes=work_modes,#tylko zrobione dla całkowicie zdalnej pracy
                description=None,
                language=None,
                apply_url=None,
                web_id=slug,
                requirements=None,
                detected_technologies=None,
    """

    """
    mozna wyciągnać dane z api:
    https://nofluffjobs.com/api/posting/junior-backend-developer-node-js-masterborn-lodz
    zamiast "junior-backend-developer-node-js-masterborn-lodz" wstawić id dowolnej oferty
    """

    print(jobOffer.url)
    #organizationURL
    if(soup.find("a", {"data-cy" : "JobOffer_CompanyProfile"}).get("href")):
        organizationURL = f'https://nofluffjobs.com{soup.find("a", {"data-cy" : "JobOffer_CompanyProfile"}).get("href")}'
    else:
        organizationURL = jobOffer.url
    #workSchedules - #nie ma na NFJ
    workSchedules = []
    #workModes
    if(response_JSON["location"]["remote"]>0):#okreslanie na podstawie liczby dni w tygodniu zdalnie
        if(response_JSON["location"]["remote"]==5):
            workModes = "3_Home-office"
        else:
            workModes = "2_Hybrid"
    else:
        workModes = ["1_Full-office"]


    #description
    offer_description = soup.find("section", {"data-cy-section":"JobOffer_Project"}).find("nfj-read-more").get_text(separator="\n").strip()

    obtainedTechnologiesList = []
    for tech in (response_JSON["requirements"]["musts"]):
        obtainedTechnologiesList.append(tech["value"])
    for tech in (response_JSON["requirements"]["languages"]):
        if(tech['type']=="MUST"):#tylko jesli obowiązkowe
            obtainedTechnologiesList.append(f'{tech["code"]} {tech.get("level") or ""}')
    """for tech in (response_JSON["requirements"]["nices"]):
        obtainedTechnologiesList.append(tech["value"])
    #nadobowiązkowe
    """

    #language
    offerLanguage, languageConfidence = langid.classify(offer_description)
    #applyURL TODO jest problem - nie potrafie znaeleźć linka zewnętrznego
    external_apply = soup.find('use', href="#md-open_in_new")
    if(external_apply):#zewnetrzna aplikacja
        applyUrl = url #TODO temporary -zanim nie ogarne tego co wyżej
    else:#wewnetrzna aplikacja
        applyUrl = url
    #web_id - brak jest webid w formie liczby, uzywany jest slug, dlatego zahashuje sluga
    hashed_web_id = generate_web_id_from_text(jobOffer.web_id, 12)
    print(hashed_web_id)

    #requirements
    requirements = []
    JobOffer_Requirements = soup.find("section", {"data-cy-section":"JobOffer_Requirements"})
    if(JobOffer_Requirements):
        requirements = JobOffer_Requirements.find("nfj-read-more").get_text(separator="\n").splitlines()
    requirements = [req.strip() for req in requirements if req.strip()]
    #print(f'requirements: {requirements}')
    #detected_technologies
    analyzed_details = analyzeOfferDetails(offerLanguage, offer_description, jobOffer.title,
                                           obtainedTechnologiesList=obtainedTechnologiesList)
    detected_technologies = analyzed_details["detected_technologies"]

    jobOffer.organization_url = organizationURL
    jobOffer.workSchedules = workSchedules
    jobOffer.workModes = workModes
    jobOffer.description = offer_description
    jobOffer.language = offerLanguage
    jobOffer.apply_url = applyUrl
    jobOffer.web_id = hashed_web_id
    jobOffer.requirements = requirements
    jobOffer.detected_technologies = detected_technologies

    return jobOffer


def scrapeNumberOfOffers(
        url="https://nofluffjobs.com/api/search/posting?withSalaryMatch=true&salaryCurrency=PLN&salaryPeriod=month&region=pl&language=pl-PL&pageSize=20&pageTo=1"):
    # get number of total pages
    print("url scrapeNumberOfOffers " + url)
    response = fetch_with_retries(url, retries=5, delay=5, method="POST", headers=nxfluffjxbs_headers, data=nxfluffjxbs_data)
    if not response:
        print(f"Skipping URL {url} due to repeated failures.")
        return
    print(response.json())
    print(find_path_to_key(response.json(), "totalCount"))
    number_of_offers = response.json()["totalCount"]
    print(f"Liczba ofert: {number_of_offers}")
    return number_of_offers



def scrapeOffersList(url, baseOfferDetailsURL = "https://justjoin.it/job-offer/", city="Łódź", province="lodz"):
    # get number of total pages
    response = fetch_with_retries(url, retries=5, delay=5, method="POST", headers=nxfluffjxbs_headers, data=nxfluffjxbs_data)
    if not response:
        print(f"Skipping URL {url} due to repeated failures.")
        return

    json_content = response.json()

    offers = []

    for job in json_content["postings"]:# normal job offers
        if job["id"]:
            location = None
            print(job["id"])
            slug = job["id"]
            if(job["location"]["places"] and type(job["location"]["places"]) is list):
                print("Multilocation")#wiele lokacji, wybrac na podstawie zapytania włąściwą lokalizację
                for job_location in job["location"]["places"]:
                    if(location==None):
                        location = job_location.get("city") or job_location.get("province") or None
                    if("province" in job_location and job_location["province"] == province):#province
                        #print(job_location)
                        slug = job_location["url"]
                        location = job_location["province"]
                        print(location)
                    if("city" in job_location and job_location["city"] == city):
                        slug = job_location["url"]
                        location = job_location["city"]
                        print(location)
                        break

            employmentTypes = []
            employmentTypes.append(nfj_employmentType_dictionary.get(job["salary"]["type"], job["salary"]["type"]))

            job_levels = []
            for job_lvl in job["seniority"]:
                job_levels.append(nfj_joblvl_dictionary.get(job_lvl.lower(), job_lvl.lower()))

            work_modes = []
            if(job["fullyRemote"]==True):
                work_modes.append(nfj_WorkModes_dictionary.get("remote", "remote"))

            offers.append(JobOffer(
                url=baseOfferDetailsURL+slug,
                date=datetime.utcfromtimestamp(job["posted"]/1000).date(), #mozna tez wziać job["renewed"]
                title=job["title"],
                organization=job["name"],
                location=location,
                job_level=job_levels,
                employmentType=employmentTypes,
                organization_url=None,
                workSchedules=None,
                workModes=work_modes,#tylko zrobione dla całkowicie zdalnej pracy
                description=None,
                language=None,
                apply_url=None,
                web_id=slug,
                requirements=None,
                detected_technologies=None,
            ))


            print(baseOfferDetailsURL+slug)
            print(job["title"])

    return offers


def scrapeOffersWithPagination(base_url, numberOfOffers,  repeat=0, baseOfferDetailsURL = "https://nofluffjobs.com/pl/job/"):
    offers = set()  # Zestaw przechowujący unikalne oferty
    runTimes = 0

    while (runTimes <= repeat):
        runTimes += 1
        page = 0

        while (
                len(offers) < numberOfOffers
        ):

            paginated_url = f"{base_url}&pageTo={0+page}"

            print(f"Scraping offers: {0+page*pageSize}/{numberOfOffers}, runTime:{runTimes}")
            offer_list = scrapeOffersList(paginated_url, baseOfferDetailsURL = baseOfferDetailsURL, city="Łódź", province="lodz")

            if not offer_list:
                print("No more offers found or reached end of results.")
                break
            offers_in_request = len(offer_list)
            print(f"offers_in_request {offers_in_request}")
            for single_offer in offer_list:
                try:
                    if single_offer not in offers:
                        offers.add(single_offer)
                    else:
                        print(f"Duplicate offer found: {single_offer.url}")
                        pass
                except KeyError:
                    print("Skipping a link without 'url'")
            print(f"Total unique offers scraped: {len(offers)}")
            page+=1

    print(f"Total unique offers scraped: {len(offers)}")
    return offers





location = "lodz"
seniority="trainee,junior"
workModes = "remote,hybrid"
pageSize = 20

urlForNumberOfOffers = f"https://nofluffjobs.com/api/search/posting?withSalaryMatch=true&salaryCurrency=PLN&salaryPeriod=month&region=pl&language=pl-PL&pageSize=20&pageTo=1"
url = f"https://nofluffjobs.com/api/search/posting?withSalaryMatch=true&salaryCurrency=PLN&salaryPeriod=month&region=pl&language=pl-PL&pageSize=20"#+&pageTo=1
# + Content-Type: application/infiniteSearch+json
# + body: {"criteria":"city=remote,hybrid seniority=trainee,junior","url":{"searchParam":"lodz"},"rawSearch":"lodz city=remote,hybrid seniority=trainee,junior ","pageSize":20,"withSalaryMatch":true}
# + method POST
nxfluffjxbs_headers = {
    "Content-Type": "application/infiniteSearch+json"
}

nxfluffjxbs_data = {
    "criteria":f"city={workModes} seniority={seniority}",
    "url":{"searchParam":f"{location}"},
    "rawSearch":f"{location} city={workModes} seniority={seniority} ",
    "pageSize":pageSize,
    "withSalaryMatch":True
}


nxfluffjxbs_data = {
    "criteria":f"city={workModes} seniority={seniority}",
    "url":{"searchParam":f"{location}"},
    "rawSearch":f"{location} city={workModes} seniority={seniority} ",
    "pageSize":pageSize,
    "withSalaryMatch":True
}

baseOfferDetailsURL = "https://nofluffjobs.com/pl/job/"



def run_NxFluffJxbs_scraper(updateInCaseOfExistingInDB=True, updateOpenAIApiPart=False):
    numberOfOffers = int(scrapeNumberOfOffers(urlForNumberOfOffers))
    if (numberOfOffers):
        offers = scrapeOffersWithPagination(url, numberOfOffers, repeat=0)
        for index, offer in enumerate(offers):
            job_offer = scrapeOfferDetails(offer)
            if (filterJobOffer(job_offer)):
                offerExists = checkIfOfferExistsInDB(web_id=job_offer.web_id, url=job_offer.url)
                if ((not offerExists.exists) or updateInCaseOfExistingInDB):
                    print("======================")
                    job_offer.skill_deficiencies = detectSkillDeficiencies(job_offer)
                    if(updateOpenAIApiPart or (not offerExists.exists)):
                        job_offer.experience_years = detectExperienceYears(job_offer)
                        print(job_offer.experience_years)
                        job_offer.skills_for_cv = generateSkillsSectionForCV(job_offer)
                    print(job_offer.url)
                    job_offer.skill_percentage = 1.0 - (float(len(job_offer.skill_deficiencies)) / float(
                        sum(len(value) for value in job_offer.detected_technologies.values())))
                    print(job_offer.skill_percentage)
                    print(
                        f"LEN: skill_deficiencies/detected_technologies: {len(job_offer.skill_deficiencies)}/{sum(len(value) for value in job_offer.detected_technologies.values())}")
                    print(
                        f"skill_deficiencies: {(job_offer.skill_deficiencies)}, detected_technologies: {(job_offer.detected_technologies)}")
                    save_job_offer_to_db(job_offer, "NoFluffJobs.com", updateInCaseOfExistingInDB=updateInCaseOfExistingInDB, updateOpenAIApiPart=updateOpenAIApiPart)