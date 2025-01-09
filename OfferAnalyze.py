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
nlp_keywords = ["doświadczenie", "znajomość", "wiedza", "umiejętność", "kompetencje",
                "experience", "skills", "Requirements", "Profile"]

# Lista języków programowania
programming_languages = [
    "Python", "JavaScript", "Java", "C#", "Ruby", "PHP",
    "TypeScript", "C++", "R", "Go", "Swift", "Kotlin",
    "Rust", "Scala", "WordPress"
]

# Lista frameworków i bibliotek
frameworks = [
    # Python frameworks
    "Django", "Flask", "FastAPI", "Pandas", "NumPy", "SciPy", "TensorFlow", "PyTorch",
    # JavaScript frameworks
    "React", "React.js", "Angular", "Vue.js", "Node.js", "Express",
    # Java frameworks
    "Spring", "Spring Boot", "Struts", "Hibernate", "JPA", "MyBatis",
    "JUnit", "TestNG", "Mockito", "Spock", "Maven", "Gradle", "Jenkins",
    "SLF4J", "Log4j", "Apache Kafka", "RabbitMQ", "JMS", "RESTEasy",
    "Jersey", "Retrofit", "Jackson", "Gson", "JAXB", "XStream",
    # C# frameworks
    "ASP.NET", "Entity Framework", "Blazor", ".Net"
    # Ruby frameworks
    "Ruby on Rails",
    # PHP frameworks
    "Laravel", "Symfony", "CodeIgniter",
    # TypeScript frameworks
    "NestJS", "Angular",
    # C++ frameworks
    "Qt", "Boost",
    # R frameworks
    "Shiny", "ggplot2", "dplyr",
    # Go frameworks
    "Gin", "Echo",
    # Swift frameworks
    "SwiftUI", "Vapor",
    # Kotlin frameworks
    "Ktor", "Spring Boot",
    # Rust frameworks
    "Actix", "Rocket", "Tokio",
    # Scala frameworks
    "Akka", "Play Framework", "Slick",
    # WordPress frameworks
    "Elementor", "WooCommerce", "Gutenberg", "Gutenify"
]

# Lista narzędzi DevOps i konteneryzacji
devops_tools = [
    "Docker", "Kubernetes", "Jenkins", "GitLab CI/CD", "Ansible", "Terraform",
    "Helm", "Prometheus", "Grafana"
]

# Lista chmur obliczeniowych
cloud_platforms = [
    "AWS", "Azure", "GCP", "Heroku", "OpenStack", "DigitalOcean"
]

# Lista baz danych
databases = [
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "SQLite",
    "MariaDB", "Oracle DB", "Cassandra", "DynamoDB", "NoSQL"
]

# Lista systemów kontroli wersji i narzędzi CI/CD
version_control_and_ci_cd = [
    "Git", "SVN", "GitHub Actions", "Bitbucket Pipelines", "CircleCI",
    "TravisCI", "Github"
]

# Lista innych technologii
other_technologies = [
    "GraphQL", "REST API", "SOAP", "WebSockets", "RabbitMQ", "Kafka"
]

# Lista języków programowania, frameworków, narzędzi i technologii
#technologies = {
#    "Języki programowania": {
#        "Python": ["Django", "Flask", "FastAPI", "Pandas", "NumPy", "SciPy", "TensorFlow", "PyTorch"],
#        "JavaScript": ["React", "React.js", "Angular", "Vue.js", "Node.js", "Express"],
#        "Java": [
#            "Spring", "Spring Boot", "Struts", "Hibernate", "JPA", "MyBatis",
#            "JUnit", "TestNG", "Mockito", "Spock",
#            "Maven", "Gradle", "Jenkins", "SLF4J", "Log4j",
#            "Apache Kafka", "RabbitMQ", "JMS", "RESTEasy", "Jersey", "Retrofit",
#            "Jackson", "Gson", "JAXB", "XStream"
#        ],
#       "C#": ["ASP.NET", "Entity Framework", "Blazor"],
#        "Ruby": ["Ruby on Rails"],
#        "PHP": ["Laravel", "Symfony", "CodeIgniter"],
#        "TypeScript": ["NestJS", "React","React.js", "Angular"],
#        "C++": ["Qt", "Boost"],
#        "R": ["Shiny", "ggplot2", "dplyr"],
#        "Go": ["Gin", "Echo"],
#        "Swift": ["SwiftUI", "Vapor"],
#        "Kotlin": ["Ktor", "Spring Boot"],
#        "Rust": ["Actix", "Rocket", "Tokio"],
#        "Scala": ["Akka", "Play Framework", "Slick"],
#        "WordPress": ["Elementor", "WooCommerce", "Gutenberg", "Gutenify"]
#    },
#    "DevOps i konteneryzacja": [
#        "Docker", "Kubernetes", "Jenkins", "GitLab CI/CD", "Ansible", "Terraform", "Helm", "Prometheus", "Grafana"
#    ],
#    "Chmury obliczeniowe": [
#        "AWS", "Azure", "GCP", "Heroku", "OpenStack", "DigitalOcean"
#    ],
#    "Bazy danych": [
#        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "SQLite", "MariaDB", "Oracle DB", "Cassandra", "DynamoDB", "NoSQL"
#    ],
#    "Systemy kontroli wersji i CI/CD": [
#        "Git", "SVN", "GitHub Actions", "Bitbucket Pipelines", "CircleCI", "TravisCI", "Github"
#    ],
#    "Inne technologie": [
#        "GraphQL", "REST API", "SOAP", "WebSockets", "RabbitMQ", "Kafka"
#    ]
#}

disqualifying_words = [
    "senior", "expert"
]

required_words = [
    "Java", "Spring", "Spring Boot", "Hibernate", "JPA",
    "Maven", "Gradle", "Jenkins", "SLF4J", "Log4j",
    "RabbitMQ", "JMS", "Jackson",
    "Python", "Django", "Flask", "FastAPI", "Pandas", "NumPy", "SciPy",
    "JavaScript", "React","React.js",
    "WordPress", "Elementor", "WooCommerce", "Gutenberg", "Gutenify"
]

my_knowledge = [
    "Java", "Spring", "Spring Boot", "Hibernate", "JPA",
    "Maven",
    "RabbitMQ",  "Jackson",
    "Python", "FastAPI", "Pandas", "NumPy", "SciPy",
    "JavaScript", "React", "React.js",
    "WordPress", "Elementor", "WooCommerce", "Gutenberg", "Gutenify"
]



def ensure_spacy_model(model_name):
    """
    Checks if the spaCy model is installed. If not, installs it.
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
    Analyzes the details of a job offer in terms of requirements and technologies, including the job title.
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
    detected_technologies = {
        "Programming Languages": [],
        "Frameworks": [],
        "DevOps Tools": [],
        "Cloud Platforms": [],
        "Databases": [],
        "Version Control and CI/CD": [],
        "Other Technologies": []
    }

    # Łączenie opisu i tytułu w jeden tekst do analizy
    combined_text = f"{offerDescription} {offerTitle}".lower()

    # Wykrywanie technologii w różnych kategoriach
    def find_with_word_boundaries(items, text):
        """Znajduje elementy w tekście za pomocą granic słów."""
        found = []
        for item in items:
            if item in {"C++", "C#", ".NET"}:  # Specjalne traktowanie tych języków
                pattern = rf'(?<!\w){re.escape(item)}(?!\w)'
            else:
                pattern = rf'\b{re.escape(item.lower())}\b'
            if re.search(pattern, text, re.IGNORECASE):
                found.append(item)
        return found

    detected_technologies["Programming Languages"] = find_with_word_boundaries(programming_languages, combined_text)
    detected_technologies["Frameworks"] = find_with_word_boundaries(frameworks, combined_text)
    detected_technologies["DevOps Tools"] = find_with_word_boundaries(devops_tools, combined_text)
    detected_technologies["Cloud Platforms"] = find_with_word_boundaries(cloud_platforms, combined_text)
    detected_technologies["Databases"] = find_with_word_boundaries(databases, combined_text)
    detected_technologies["Version Control and CI/CD"] = find_with_word_boundaries(version_control_and_ci_cd, combined_text)
    detected_technologies["Other Technologies"] = find_with_word_boundaries(other_technologies, combined_text)


    # Zwracanie wyników
    return {
        "requirements": requirements,
        "detected_technologies": detected_technologies
    }



def filterJobOffer(job_offer):
    """
    Filters a job offer based on disqualifying words in the title and required technologies in detected_technologies.

    1. Checks if the job title contains any disqualifying words (e.g., "senior").
    2. Checks if the detected technologies match any of the required words (e.g., programming languages, frameworks).
    3. Accepts the offer if required words are found; rejects otherwise.

    Filtruje ofertę pracy na podstawie słów dyskwalifikujących w tytule oraz wymaganych technologii w detected_technologies.

    1. Sprawdza, czy tytuł oferty zawiera jakiekolwiek słowa dyskwalifikujące (np. "senior").
    2. Sprawdza, czy wykryte technologie pasują do listy wymaganych słów (np. języki programowania, frameworki).
    3. Akceptuje ofertę, jeśli znaleziono wymagane słowa; odrzuca w przeciwnym wypadku.

    :param job_offer: An object representing a job offer, containing attributes like title, job_level, and detected_technologies.
    :return: True if the offer meets the criteria, False otherwise.

    """

    text_to_search_4_disqualifying_words = f"{job_offer.title}".lower()

    print(job_offer.job_level)
    # Sprawdzenie obecności słów dyskwalifikujących
    for word in disqualifying_words:
        if word.lower() in text_to_search_4_disqualifying_words:
            print(f"Oferta odrzucona z powodu słowa dyskwalifikującego: {word}")
            return False



    # Sprawdzanie słów wymaganych w detected_technologies
    found_required_words = set()
    for category, items in job_offer.detected_technologies.items():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, tuple):  # Jeśli item to krotka (np. język i frameworki)
                    language, frameworks = item
                    if language.lower() in (word.lower() for word in required_words):
                        found_required_words.add(language)
                    found_required_words.update(
                        [fw for fw in frameworks if fw.lower() in (word.lower() for word in required_words)]
                    )
                elif isinstance(item, str):  # Jeśli item to string (prosta technologia)
                    if item.lower() in (word.lower() for word in required_words):
                        found_required_words.add(item)

    # Jeśli znaleziono wymagane słowa, akceptujemy ofertę
    if found_required_words:
        print(f"Oferta spełnia wymagania. Znalezione słowa kluczowe: {', '.join(found_required_words)}")
        return True

    # Jeśli nie znaleziono wymaganych słów, odrzuć ofertę
    print("Oferta odrzucona: brak wymaganych słów kluczowych.")
    return False


def detectSkillDeficiencies(job_offer):
    """
    Identifies technologies mentioned in the job offer that are not present in the provided list of known technologies.
    Identyfikuje technologie wymienione w ofercie pracy, które nie znajdują się na podanej liście znanych technologii.

    :param job_offer: A job offer object containing detected_technologies.
    :return: A list of technologies that are missing in the user's knowledge.
    """
    missing_technologies = set()
    known_technologies = set([tech.lower() for tech in my_knowledge])  # Normalizacja do lowercase

    # Przeszukiwanie detected_technologies w ofercie
    for category, items in job_offer.detected_technologies.items():
        if isinstance(items, list):  # Prosta lista technologii
            for item in items:
                if isinstance(item, str) and item.lower() not in known_technologies:
                    missing_technologies.add(item)
        elif isinstance(items, dict):  # Języki programowania z frameworkami
            for language, frameworks in items.items():
                # Sprawdzanie języka programowania
                if language.lower() not in known_technologies:
                    missing_technologies.add(language)
                # Sprawdzanie frameworków
                for framework in frameworks:
                    if framework.lower() not in known_technologies:
                        missing_technologies.add(framework)
        elif isinstance(items, tuple):  # Obsługa krotek (jeśli wystąpią)
            for item in items:
                if isinstance(item, str) and item.lower() not in known_technologies:
                    missing_technologies.add(item)

    # Zamiana na listę i sortowanie dla czytelności
    missing_technologies = sorted(missing_technologies)

    # Wyświetlanie wyników
    if missing_technologies:
        print("Brakujące technologie w tej ofercie:")
        for tech in missing_technologies:
            print(f"- {tech}")
    else:
        print("Nie znaleziono braków w Twojej wiedzy dla tej oferty.")

    return missing_technologies