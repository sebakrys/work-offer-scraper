import re
import string

import spacy
import importlib
import subprocess



# Mapowanie języków na modele spaCy
LANGUAGE_MODEL_MAP = {
    "pl": "pl_core_news_sm",
    "en": "en_core_web_sm"
}

# Wyodrębnij zdania zawierające typowe słowa związane z wymaganiami
nlp_keywords = ["doświadczenie", "znajomość", "wiedza", "umiejętność", "kompetencje"
                                                                   "experience", "skills", "Requirements", "Profile"]

# Lista języków programowania, frameworków, narzędzi i technologii
technologies = {
    "Języki programowania": {
        "Python": ["Django", "Flask", "FastAPI", "Pandas", "NumPy", "SciPy", "TensorFlow", "PyTorch"],
        "JavaScript": ["React", "Angular", "Vue.js", "Node.js", "Express"],
        "Java": [
            "Spring", "Spring Boot", "Struts", "Hibernate", "JPA", "MyBatis",
            "JUnit", "TestNG", "Mockito", "Spock",
            "Maven", "Gradle", "Jenkins", "SLF4J", "Log4j",
            "Apache Kafka", "RabbitMQ", "JMS", "RESTEasy", "Jersey", "Retrofit",
            "Jackson", "Gson", "JAXB", "XStream"
        ],
        "C#": ["ASP.NET", "Entity Framework", "Blazor"],
        "Ruby": ["Ruby on Rails"],
        "PHP": ["Laravel", "Symfony", "CodeIgniter"],
        "TypeScript": ["NestJS", "React", "Angular"],
        "C++": ["Qt", "Boost"],
        "R": ["Shiny", "ggplot2", "dplyr"],
        "Go": ["Gin", "Echo"],
        "Swift": ["SwiftUI", "Vapor"],
        "Kotlin": ["Ktor", "Spring Boot"],
        "Rust": ["Actix", "Rocket", "Tokio"],
        "Scala": ["Akka", "Play Framework", "Slick"],
        "WordPress": ["Elementor", "WooCommerce", "Gutenberg", "Gutenify"]
    },
    "DevOps i konteneryzacja": [
        "Docker", "Kubernetes", "Jenkins", "GitLab CI/CD", "Ansible", "Terraform", "Helm", "Prometheus", "Grafana"
    ],
    "Chmury obliczeniowe": [
        "AWS", "Azure", "GCP", "Heroku", "OpenStack", "DigitalOcean"
    ],
    "Bazy danych": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "SQLite", "MariaDB", "Oracle DB", "Cassandra", "DynamoDB", "NoSQL"
    ],
    "Systemy kontroli wersji i CI/CD": [
        "Git", "SVN", "GitHub Actions", "Bitbucket Pipelines", "CircleCI", "TravisCI", "Github"
    ],
    "Inne technologie": [
        "GraphQL", "REST API", "SOAP", "WebSockets", "RabbitMQ", "Kafka"
    ]
}


def ensure_spacy_model(model_name):
    """
    Sprawdza, czy model spaCy jest zainstalowany. Jeśli nie, instaluje go.
    """
    try:
        # Spróbuj zaimportować model
        importlib.import_module(model_name)
    except ImportError:
        print(f"Model {model_name} nie jest zainstalowany. Instaluję...")
        subprocess.run(["python", "-m", "spacy", "download", model_name], check=True)
        print(f"Model {model_name} został zainstalowany.")
    else:
        #print(f"Model {model_name} jest już zainstalowany.")
        pass

def get_nlp_model_for_text(language):
    model_name = LANGUAGE_MODEL_MAP.get(language)

    if model_name:
        ensure_spacy_model(model_name)
        return spacy.load(model_name)
    else:
        raise ValueError(f"Brak modelu spaCy dla wykrytego języka: {language}")


def analyzeOfferDetails(offerLanguage, offerDescription, offerTitle):
    """
    Analizuje szczegóły oferty pracy pod kątem wymagań i technologii, uwzględniając tytuł oferty.
    :param offerLanguage: Język tekstu (np. "en", "pl").
    :param offerDescription: Opis oferty pracy jako tekst.
    :param offerTitle: Tytuł oferty pracy jako tekst.
    :return: Słownik z wymaganiami i wykrytymi technologiami.
    """
    # Pobierz odpowiedni model NLP dla danego języka
    nlp = get_nlp_model_for_text(offerLanguage)

    # Analiza tekstu z NLP
    doc = nlp(offerDescription)

    # Wyszukiwanie zdań z wymaganiami w opisie
    requirements = [
        sent.text.strip() for sent in doc.sents
        if any(keyword in sent.text.lower() for keyword in nlp_keywords)
    ]

    # Wykrywanie technologii w tytule i opisie
    detected_technologies = {}

    for category, items in technologies.items():
        detected_technologies[category] = []

        if isinstance(items, dict):  # Obsługa języków z frameworkami
            for language, frameworks in items.items():
                # Specjalne traktowanie języków z symbolami (np. C++)
                if re.search(rf'\b{re.escape(language)}\b', f"{offerDescription} {offerTitle}", re.IGNORECASE):
                    frameworks_found = [
                        framework for framework in frameworks
                        if re.search(rf'\b{re.escape(framework)}\b', f"{offerDescription} {offerTitle}", re.IGNORECASE)
                    ]
                    detected_technologies[category].append((language, frameworks_found))
        else:  # Prosta lista technologii
            detected_technologies[category] = [
                item for item in items if re.search(rf'\b{re.escape(item)}\b', f"{offerDescription} {offerTitle}", re.IGNORECASE)
            ]

    # Dodatkowe sprawdzanie dla C++ i podobnych języków
    if "C++" in f"{offerDescription} {offerTitle}":
        detected_technologies["Języki programowania"].append(("C++", technologies["Języki programowania"]["C++"]))
    if "C#" in f"{offerDescription} {offerTitle}":
        detected_technologies["Języki programowania"].append(("C#", technologies["Języki programowania"]["C#"]))

    # Zwracanie wyników
    return {
        "requirements": requirements,
        "detected_technologies": detected_technologies
    }
