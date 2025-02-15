import os
from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, JSON, ARRAY, BigInteger, Double, func, \
    DateTime, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Ładowanie zmiennych środowiskowych
load_dotenv()

# Konfiguracja bazy danych
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")

# SQLAlchemy ORM konfiguracja
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Definicja modelu JobOffer

class JobOfferDB(Base):
    __tablename__ = "job_offers"

    id = Column(Integer, primary_key=True, index=True)
    applied = Column(Boolean, default=False)  # new
    hidden = Column(Boolean, default=False)
    url = Column(Text, nullable=False)
    date = Column(Date)
    title = Column(Text)
    skill_deficiencies = Column(ARRAY(Text))
    skill_percentage = Column(Double)
    skills_for_cv = Column(Text, default="")
    experience_years = Column(ARRAY(Double), default=[])
    organization = Column(Text)
    organization_url = Column(Text)
    location = Column(Text)
    language = Column(String(10))
    job_level = Column(ARRAY(Text))
    employmentType = Column(ARRAY(Text), default=[])  # new (rodzaj zatrudnienia, np. Umowa o pracę, B2B)
    workSchedules = Column(ARRAY(Text), default=[])  # new (Etat, pełny, niepełny)
    workModes = Column(ARRAY(Text), default=[])  # new (Hybrydowo, zdalnie, stacjonarnie)
    apply_url = Column(Text)
    web_id = Column(BigInteger)
    requirements = Column(ARRAY(Text))
    detected_technologies = Column(JSON)
    description = Column(Text)
    source = Column(Text)
    first_scrape_date = Column(DateTime, default=func.now())  # Data pierwszego zrzutu
    scrape_date = Column(DateTime, default=func.now(), onupdate=func.now())  # Data ostatniej aktualizacji


# Inicjalizacja bazy danych
def init_db():
    """
    Tworzy schematy w bazie danych, jeśli jeszcze nie istnieją.
    """
    Base.metadata.create_all(bind=engine)


def checkIfOfferExistsInDB(web_id, url, close_session_at_the_end=True):
    """
    checks if offer with following `web_id` or `url` exists in data base.

    :param web_id: ID from web to check.
    :param url: URL of offer to check.
    :return: True, if offer exists, False if it doesn't.
    """
    session = SessionLocal()
    try:
        # Sprawdzenie, czy oferta już istnieje w bazie danych
        existing_offer = session.query(JobOfferDB).filter(
            (JobOfferDB.web_id == web_id) | (JobOfferDB.url == url)
        ).first()
        return type("OfferCheckResult", (object,), {
            "exists": existing_offer is not None,
            "offer": existing_offer
        })()
    except Exception as e:
        session.rollback()
        print(f"Błąd podczas wczytywania oferty: {e}")
        return type("OfferCheckResult", (object,), {
            "exists": False,
            "offer": None
        })()
    finally:
        if(close_session_at_the_end):
            session.close()



def save_job_offer_to_db(job_offer, source, updateInCaseOfExistingInDB=True, updateOpenAIApiPart=False):
    """
    Zapisuje ofertę pracy do bazy danych.

    :param job_offer: Słownik zawierający dane oferty pracy.
    :return: True, jeśli zapisano ofertę, False w przypadku duplikatu lub błędu.
    """
    session = SessionLocal()
    try:

        # Sprawdzenie, czy oferta już istnieje w bazie danych
        offerExists = checkIfOfferExistsInDB(web_id=job_offer.web_id, url=job_offer.url, close_session_at_the_end=False)

        if offerExists.exists:
            existing_offer = session.merge(offerExists.offer)
            print(f"Oferta o ID {job_offer.web_id} już istnieje.")
            if (updateInCaseOfExistingInDB):
                print("Aktualizowanie...")
                # Aktualizacja istniejącej oferty
                existing_offer.url = job_offer.url
                existing_offer.date = job_offer.date
                existing_offer.title = job_offer.title
                existing_offer.skill_deficiencies = job_offer.skill_deficiencies
                existing_offer.skill_percentage = job_offer.skill_percentage
                existing_offer.job_level = job_offer.job_level
                existing_offer.organization = job_offer.organization
                existing_offer.organization_url = job_offer.organization_url
                existing_offer.location = job_offer.location
                existing_offer.language = job_offer.language
                if (updateOpenAIApiPart):
                    existing_offer.experience_years = job_offer.experience_years
                    existing_offer.skills_for_cv = job_offer.skills_for_cv
                existing_offer.employmentType = job_offer.employmentType  # new (rodzaj zatrudnienia, np. Umowa o pracę, B2B)
                existing_offer.workSchedules = job_offer.workSchedules  # new (Etat, pełny, niepełny)
                existing_offer.workModes = job_offer.workModes  # new (Hybrydowo, zdalnie, stacjonarnie)
                existing_offer.apply_url = job_offer.apply_url
                existing_offer.requirements = job_offer.requirements
                existing_offer.detected_technologies = job_offer.detected_technologies
                existing_offer.description = job_offer.description
                existing_offer.source = source

                session.commit()
                print(f"Oferta o ID {job_offer.web_id} została zaktualizowana.")
            return True

        # Tworzenie i zapisywanie nowej oferty
        new_offer = JobOfferDB(
            url=job_offer.url,
            date=job_offer.date,
            title=job_offer.title,
            skill_deficiencies=job_offer.skill_deficiencies,
            skill_percentage=job_offer.skill_percentage,
            skills_for_cv=job_offer.skills_for_cv,
            experience_years=job_offer.experience_years,
            job_level=job_offer.job_level,
            organization=job_offer.organization,
            organization_url=job_offer.organization_url,
            location=job_offer.location,
            language=job_offer.language,
            employmentType=job_offer.employmentType,  # new (rodzaj zatrudnienia, np. Umowa o pracę, B2B)
            workSchedules = job_offer.workSchedules,  # new (Etat, pełny, niepełny)
            workModes = job_offer.workModes,  # new (Hybrydowo, zdalnie, stacjonarnie)
            apply_url=job_offer.apply_url,
            web_id=job_offer.web_id,
            requirements=job_offer.requirements,
            detected_technologies=job_offer.detected_technologies,
            description=job_offer.description,
            source=source,

        )
        session.add(new_offer)
        session.commit()
        print(f"Oferta o ID {job_offer.web_id} została zapisana w bazie danych.")
        return True
    except Exception as e:
        session.rollback()
        print(f"Błąd podczas zapisywania oferty: {e}")
        return False
    finally:
        session.close()


# Inicjalizacja bazy danych przy imporcie modułu
init_db()
