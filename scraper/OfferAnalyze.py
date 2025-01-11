import os
import re
import string

import openai
import spacy
import importlib
import subprocess



# Mapowanie języków na modele spaCy
from openai import OpenAI

from scraper.database import checkIfOfferExistsInDB

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
    "Rust", "Scala", "WordPress", "SQL",
    "HTML", "CSS", "Bash", "Perl", "Haskell"
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
    "ASP.NET", "Entity Framework", "Blazor", ".NET",
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
    "Elementor", "WooCommerce", "Gutenberg", "Gutenify",
    # New additions
    "Cypress", "Jest", "Bootstrap", "Tailwind", "Next.js",
    "Nest.js", "RxJS", "NgRx", "Prisma", "OpenAPI", "Redux",
    "Foundation", "Blazor"
]

# Lista narzędzi DevOps i konteneryzacji
devops_tools = [
    "Docker", "Kubernetes", "Jenkins", "GitLab CI/CD", "Ansible", "Terraform",
    "Helm", "Prometheus", "Grafana",
    # New additions
    "Bitbucket", "TeamCity", "SonarQube", "Argo CD", "Azure DevOps", "Nomad", "Spinnaker"
]

# Lista chmur obliczeniowych
cloud_platforms = [
    "AWS", "Azure", "GCP", "Heroku", "OpenStack", "DigitalOcean",
    # New additions
    "Google Cloud Platform", "Microsoft Azure", "Azure Monitor", "Vercel"
]

# Lista baz danych
databases = [
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "SQLite",
    "MariaDB", "Oracle DB", "Cassandra", "DynamoDB", "NoSQL",
    # New additions
    "ArangoDB", "Hazelcast", "Azure SQL", "MS SQL", "Redshift", "S3", "CosmosDB", "PL/SQL"
]

# Lista systemów kontroli wersji i narzędzi CI/CD
version_control_and_ci_cd = [
    "Git", "SVN", "GitHub Actions", "Bitbucket Pipelines", "CircleCI",
    "TravisCI", "Github",
    # New additions
    "GitLab", "GitHub", "GitHub Enterprise"
]

# Lista innych technologii
other_technologies = [
    "GraphQL", "REST API", "SOAP", "WebSockets", "RabbitMQ", "Kafka",
    # New additions
    "WebAPI", "OpenVPN", "VBA", "Microservices"
]





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
    "Java", "Python", "JavaScript", "HTML", "CSS", "WordPress", "SQL", "Bash",

    "Spring", "Spring Boot", "Hibernate", "JPA", "Maven",
    "RabbitMQ",  "Jackson",

    "FastAPI", "Pandas", "NumPy", "SciPy",

    "React", "React.js",

    "Elementor", "WooCommerce", "Gutenberg", "Gutenify",

    "GCP", "Google Cloud Platform", "REST API", "PostgreSQL",
    "Git", "Github",

    "Docker", "Bootstrap", "Kubernetes",

    "Microservices", "OpenVPN",
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

    try:
        if model_name:
            ensure_spacy_model(model_name)
            return spacy.load(model_name)
        else:
            print(f"Brak modelu spaCy dla wykrytego języka: {language}. Użycie modelu domyślnego 'en_core_web_sm'.")
            ensure_spacy_model("en_core_web_sm")
            return spacy.load("en_core_web_sm")
    except Exception as e:
        print(f"Błąd podczas ładowania modelu spaCy dla języka {language}: {e}")
        # Możesz zwrócić `None` lub inny fallback tutaj, jeśli chcesz.
        return None


def detectExperienceYears(job_offer, disable_OpenAI=True):
    offerDescription = job_offer.description
    offerLanguage = job_offer.language
    if(disable_OpenAI):
        offerExperienceYears = extract_experience_years_with_context_nlp(description=offerDescription, language_code=offerLanguage)
    else:
        extract_experience_years_with_context_nlp(description=offerDescription, language_code=offerLanguage)
        offerExperienceYears = extract_experience_years_with_openai(description=offerDescription,
                                                                    language_code=offerLanguage)
    return offerExperienceYears

def extract_experience_years_with_openai(description, language_code):
    """
    Extracts required years or months of experience from a job description using OpenAI's GPT model.

    :param description: Job description as a string.
    :param language_code: Language code of the description (e.g., 'pl' or 'en').
    :return: List of extracted experience values in years.
    """
    # Prompt dostosowany do języka
    if language_code == "pl":
        prompt = f"""
        W opisie oferty pracy poniżej znajdź wszystkie odniesienia do wymaganego doświadczenia zawodowego 
        w latach lub miesiącach. Wyraź wynik w latach, uwzględniając konwersję miesięcy na lata (12 miesięcy = 1 rok). Jeśli brak informacji to wypisz 0. Jeśli jest podane w postaci zakresu (np. 3-4 lata) podaj niższą wartość.
        Wypisz same liczby. Nie sumuj oddzielnych doświadczeń, lecz je wypisz. Oto opis oferty pracy:

        {description}
        """
    else:
        prompt = f"""
        From the job description below, find all references to required professional experience 
        in years or months. Express the result in years, including converting months into years 
        (12 months = 1 year). If there is no information, print 0. In case of range (eg. 3-4 years), provide lower value. Provide only the numbers. Don't sum separate experiences, but write out. Here is the job description:

        {description}
        """
    try:
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
            organization=os.environ.get("OPENAI_ORG_ID"),
        )
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            model="gpt-4o-mini",
        )
        # Pobranie i przetworzenie odpowiedzi
        extracted_text = response.choices[0].message.content.strip()
        #print(extracted_text)
        years = []
        # Wyodrębnianie liczb z odpowiedzi
        for part in extracted_text.split():
            try:
                years.append(float(part))
            except ValueError:
                pass  # Pomija fragmenty, które nie są liczbami
        print(f"Years experience(OpenAI): {years}")
        return years

    except Exception as e:
        # General exception handling
        print(f"An error occurred: {e}")
        return []
def extract_experience_years_with_context_nlp(description, language_code):
    """
    Extracts required years or months of experience from a job description,
    supporting both Polish and English languages.

    Wyciąga wymagane lata lub miesiące doświadczenia z opisu oferty pracy,
    obsługując języki polski i angielski.

    Jak działa:
    1. **Ładowanie modelu językowego**:
       - Na podstawie podanego kodu języka (`language_code`) funkcja `get_nlp_model_for_text`
         ładuje odpowiedni model spaCy (np. dla 'pl' lub 'en').

    2. **Słowa kluczowe i jednostki czasu**:
       - Słownik `keywords` zawiera:
         - **Słowa kluczowe**: Wyrażenia związane z doświadczeniem (np. „doświadczenie”, „experience”).
         - **Słowa wykluczające**: Frazy, które wskazują, że zdanie nie dotyczy wymagań doświadczenia
           (np. „nasza firma ma 10 lat doświadczenia na rynku”).
         - **Jednostki czasu**: Słowa takie jak „rok”, „lata”, „months” wraz z przelicznikiem na lata
           (np. „m-cy” odpowiada 1/12 roku).

    3. **Analiza tekstu z spaCy**:
       - Tekst opisu (`description`) jest analizowany przez spaCy.
       - Model dzieli tekst na zdania i tokeny (pojedyncze wyrazy, liczby itp.).

    4. **Iteracja po zdaniach**:
       - Funkcja przegląda każde zdanie w opisie:
         - Szuka tokenów będących liczbami (`token.like_num`).
         - Sprawdza, czy kolejny token jest jednostką czasu (np. „lata”, „years”).
         - Analizuje kontekst zdania pod kątem obecności słów kluczowych (np. „doświadczenie”, „experience”)
           i braku słów wykluczających.

    5. **Konwersja na lata doświadczenia**:
       - Jeśli zdanie spełnia kryteria, liczba (np. „3”) jest przeliczana na lata
         na podstawie jednostki czasu (np. „m-cy” to 1/12 roku).
       - Wynik jest dodawany do listy `years`.

    6. **Zwracanie wyniku**:
       - Funkcja zwraca listę wartości odpowiadających wymaganym latom doświadczenia w latach.

    Przykład działania:
    - Dla opisu w języku polskim:
      ```python
      description_pl = "Co najmniej 3-letnie doświadczenie zawodowe oraz 6 m-cy doświadczenia w implementacji rozwiązań."
      extract_experience_years_with_context(description_pl, "pl")
      # Wynik: [3.0, 0.5]
      ```
    - Dla opisu w języku angielskim:
      ```python
      description_en = "We require at least 4 years of experience in backend development and 6 months with Node.js."
      extract_experience_years_with_context(description_en, "en")
      # Wynik: [4.0, 0.5]
      ```

    Kluczowe punkty:
    - Funkcja obsługuje dwa języki (polski i angielski).
    - Odrzuca zdania niezwiązane z wymaganym doświadczeniem za pomocą słów wykluczających.
    - Przelicza miesiące na lata, aby zwrócić spójny wynik.


    :param description: Job description as a string.
    :param language_code: Language code of the description (e.g., 'pl' or 'en').
    :return: List of extracted experience values in years.
    """


    # Load the appropriate spaCy NLP model for the given language
    nlp = get_nlp_model_for_text(language_code)

    # keywords and timeunits for both languages (pl, en)
    keywords = {
        "pl": {
            "experience": ["doświadczenie", "praca", "stanowisku", "poziom", "programowanie", "języku"],
            "exclude": ["nasza firma", "jesteśmy na rynku", "lat na rynku"],
            "time_units": {"lat": 1, "roku": 1, "lata": 1, "rok": 1, "m-cy": 1/12, "miesiące": 1/12, "miesięcy": 1/12}
        },
        "en": {
            "experience": ["experience", "years", "months", "position", "role", "programming"],
            "exclude": ["our company", "we have been in the market", "years in the market"],
            "time_units": {"years": 1, "year": 1, "months": 1/12, "month": 1/12}
        }
    }

    # Map words to numbers (English only for now)
    word_to_number = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,

        "jeden": 1, "dwa": 2, "trzy": 3, "cztery": 4, "pięć": 5, "sześć": 6,
        "siedem": 7, "osiem": 8, "dziewięć": 9, "dziesięć": 10, "jedynaście": 11, "dwanaście": 12
    }

    # Get the relevant keywords and time units based on the language
    lang_data = keywords.get(language_code, keywords["en"])  # Default to English
    experience_keywords = lang_data["experience"]
    exclusion_keywords = lang_data["exclude"]
    time_units = lang_data["time_units"]

    # Process the description with spaCy
    doc = nlp(description)
    years = []

    for sent in doc.sents:
        for token in sent:
            # Check if token is a number or a written number
            try:
                num_value = float(token.text)
            except ValueError:
                num_value = word_to_number.get(token.text.lower(), None)
            # If a valid number is found
            if num_value is not None:
                next_token = token.nbor(1) if token.i + 1 < len(doc) else None
                if next_token and next_token.text.lower() in time_units:
                    context = sent.text.lower()
                    # Check if the sentence contains relevant keywords
                    if any(keyword in context for keyword in experience_keywords) and not any(
                            exclusion in context for exclusion in exclusion_keywords):
                        experience_in_years = num_value * time_units[next_token.text.lower()]
                        years.append(round(experience_in_years, 2))

    # Debug output for extracted years
    print(f"Years experience(NLP): {years}")
    return years


def analyzeOfferDetails(offerLanguage, offerDescription, offerTitle, obtainedTechnologiesList=[]):
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

    # Łączenie opisu, tytułu i listy technologii w jeden tekst do analizy
    combined_text = f"{offerDescription} {offerTitle} {' '.join(obtainedTechnologiesList)}".lower()

    # Wykrywanie technologii w różnych kategoriach
    def find_with_word_boundaries(items, text):
        """Finds items in the text using word boundaries and special handling for cases like C#, C++, .NET."""
        found = []
        for item in items:
            if item == ".NET":  # Specific handling for .NET
                pattern = r'(?<!\w)\.NET(?!\w|\d)'
            elif item in {"C++", "C#"}:  # Specific handling for C++ and C#
                pattern = rf'(?<!\w){re.escape(item)}(?!\w)'
            else:  # General case for other technologies
                pattern = rf'\b{re.escape(item)}\b'
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
        # w tytule
        if word.lower() in text_to_search_4_disqualifying_words:
            print(f"Oferta odrzucona z powodu słowa dyskwalifikującego: {word}")
            return False
        # w job_lvl
        for lvl in job_offer.job_level:
            if (lvl.lower() in word.lower()):
                print(f"Oferta odrzucona z powodu poziomu dyskwalifikującego: {word}")
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
        print(f"Oferta spełnia wymagania. Znalezione słowa kluczowe: ")#{' '.join(found_required_words)}
        for w in found_required_words:
            print(f"- {w}")
        return True

    # Jeśli nie znaleziono wymaganych słów, odrzuć ofertę
    #print("Oferta odrzucona: brak wymaganych słów kluczowych.")
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
                if isinstance(item, str) and not (item.lower() in known_technologies):
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

def generateSkillsSectionForCV(job_offer):
    """
    generate Skills section for CV using OpenAI's GPT model.

    :param job_offer: Job offer object
    :return: String with skills section
    """
    language_code = job_offer.language
    # Prompt dostosowany do języka
    if language_code == "pl":
        prompt = f"""
        Na podstawie mojej listy umiejętności i wiedzy:
        {my_knowledge}, Język angielski na poziomie B2 (Certyfikat TOEIC® Listening & Reading: 820),
        Certyfikaty HackerRank: Python, Software Engineer, React, Java.
        
        Przygotuj sekcję „Umiejętności” do mojego CV. Użyj tylko tych umiejętności, które są istotne dla poniższej oferty pracy:
        {job_offer.description}
        Nie używaj żadnych umiejętności, których nie ma na mojej liście wiedzy.
        Uwzględnij wyłącznie technologie i narzędzia, które są wymienione zarówno w ofercie pracy, jak i na mojej liście wiedzy.
        Sekcja „Umiejętności” powinna być możliwie jak najkrótsza.
        Na koniec podaj zwięzłą sekcję „Umiejętności” jako swoją ostateczną odpowiedź, niech zawiera 6-8 punktów.
        Jako szablon wykorzystaj:
        "
•	Programowanie w Python, Java, C
•	Zarządzanie projektami i koordynacja zespołów
•	Biegłość w pracy z Git, Spring, React, MongoDB, PostgreSQL
•	Certyfikaty HackerRank: Python, Software Engineer, React, Java
•	Testowanie API za pomocą Postman
•	Znajomość FastAPI, Docker and Kubernetes
•	Praktyczna znajomość i umiejętność korzystania z usług Google Cloud
•	Język angielski na poziomie B2 (Certyfikat TOEIC® Listening & Reading: 820)
•	Doświadczenie w integracji systemów i tworzeniu API"

Zacznij Sekcję „Umiejętności” słowem [START], a zakończ [END].
        """
    else:
        prompt = f"""
        Based on my list of skills, knowledge:
        {my_knowledge}, English B2, TOEIC® Listening & Reading Certificate: 820,
        HackerRank Certifications: Python, Software Engineer, React, Java.
        Prepare "Skills" section for my CV. Use only skills relevant for job offer with description below:
        {job_offer.description}
        Do not use any skills that are not present in my knowledge.
        Only include technologies and tools explicitly mentioned in both the job offer and my own knowledge list.
        Make “Skills” section as short as possible.
        Finally, provide a concise “Skills” section as your final answer, using 6-8 points.
        As a template use following:
        "
•	Programming in X, Y, Z
•	Project management and team coordination
•	Proficiency in Git, Spring, React, MongoDB, PostgreSQL
•	HackerRank Certifications: Python, Software Engineer, Java, React
•	Familiarity with Docker and Kubernetes
•	Practical knowledge and ability to utilize Google Cloud services.
•	English B2, TOEIC® Listening & Reading Certificate: 820"

At the beginning of “Skills” section use [START], and at end [END].
        """
    try:
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
            organization=os.environ.get("OPENAI_ORG_ID"),
        )
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            model="gpt-4o-mini",
        )
        # Pobranie i przetworzenie odpowiedzi
        extracted_text = response.choices[0].message.content.strip()
        #print(prompt)
        print(extracted_text)
        skills=""

        start = extracted_text.find("[START]") + len("[START]")  # Indeks po [START]
        end = extracted_text.find("[END]")  # Indeks początku [STOP]
        print(f"[START]:{start} [END]:{end}")

        if start != -1 and end != -1:
            skills = (extracted_text[start:end]).strip()
            print(skills)
        else:
            print("No match found")
        return skills

    except Exception as e:
        # General exception handling
        print(f"An error occurred: {e}")
        return ""