import os
from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, JSON, ARRAY, BigInteger, Double
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
    url = Column(Text, nullable=False)
    date = Column(Date)
    title = Column(Text)
    skill_deficiencies = Column(ARRAY(Text))
    skill_percentage = Column(Double)
    organization = Column(Text)
    organization_url = Column(Text)
    location = Column(Text)
    language = Column(String(10))
    job_level = Column(Text)
    apply_url = Column(Text)
    web_id = Column(BigInteger)
    requirements = Column(ARRAY(Text))
    detected_technologies = Column(JSON)
    description = Column(Text)


# Inicjalizacja bazy danych
def init_db():
    """
    Tworzy schematy w bazie danych, jeśli jeszcze nie istnieją.
    """
    Base.metadata.create_all(bind=engine)


def save_job_offer_to_db(job_offer):
    """
    Zapisuje ofertę pracy do bazy danych.

    :param job_offer: Słownik zawierający dane oferty pracy.
    :return: True, jeśli zapisano ofertę, False w przypadku duplikatu lub błędu.
    """
    session = SessionLocal()
    try:
        # Sprawdzenie, czy oferta już istnieje w bazie danych
        existing_offer = session.query(JobOfferDB).filter(
            (JobOfferDB.web_id == job_offer.web_id) | (JobOfferDB.url == job_offer.url)
        ).first()

        if existing_offer:
            print(f"Oferta o ID {job_offer.web_id} już istnieje w bazie danych.")
            return False

        # Tworzenie i zapisywanie nowej oferty
        new_offer = JobOfferDB(
            url=job_offer.url,
            date=job_offer.date,
            title=job_offer.title,
            skill_deficiencies=job_offer.skill_deficiencies,
            skill_percentage=job_offer.skill_percentage,
            job_level=job_offer.job_level,
            organization=job_offer.organization,
            organization_url=job_offer.organization_url,
            location=job_offer.location,
            language=job_offer.language,
            apply_url=job_offer.apply_url,
            web_id=job_offer.web_id,
            requirements=job_offer.requirements,
            detected_technologies=job_offer.detected_technologies,
            description=job_offer.description
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
