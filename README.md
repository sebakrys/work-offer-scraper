# Job Scraper & Flask Web App

This repository consists of two main components:

1. `flask_app`: A Flask-based web application that provides an API and a front-end for managing and visualizing job offers.
2. `scraper`: A set of scrapers to collect job offers from various sources and store them in a PostgreSQL database.

## Features

### Flask App
- **API Endpoints**:
  - `/api/data`: Fetch all job offers from the database in JSON format.
  - `/api/update_applied`: Update the `applied` status of a job offer.
- **Front-End**:
  - A dynamic table displaying job offers with sorting and filtering capabilities.
  - Ability to copy required skills to the clipboard and update the applied status directly from the UI.

### Scraper
- **Sources Supported**:
  - Various job boards (e.g., LixkedIx, PrxcujPX, NxFluffJxbs).
- **Data Extracted**:
  - Job title, organization, location, required skills, experience, job level, application URL, and more.
- **Enhancements**:
  - NLP-based analysis for skill extraction.
  - OpenAI GPT integration for generating CV-ready skills sections and extracting experience requirements.

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Node.js (for front-end dependencies)
- OpenAI API key (optional for advanced features)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/sebakrys/work-offer-scraper.git
   cd work-offer-scraper
   ```

2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file with the following variables:
   ```env
   DATABASE_URL=your_postgresql_connection_string
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_ORG_ID=your_openai_org_id
   ```

4. Initialize the database:
   ```bash
   python scraper/database.py
   ```

5. Run the Flask app:
   ```bash
   cd flask_app
   python app.py
   ```

6. Start the scrapers:
   ```bash
   cd scraper
   python main.py
   ```

## Usage

### Flask App
- Navigate to `http://127.0.0.1:5000` to access the front-end.
- Use the API endpoints to fetch or update data programmatically.

### Scraper
- Follow the prompts to choose whether to update existing records or use OpenAI-based enhancements.
- Scraped data will be automatically stored in the database.


## Technologies Used

- **Back-End**: Flask, SQLAlchemy
- **Front-End**: HTML, CSS, JavaScript (DataTables)
- **Database**: PostgreSQL
- **Scraping**: Playwright, BeautifulSoup
- **NLP & AI**: spaCy, OpenAI GPT

## Future Improvements
- Enhance the front-end with advanced filtering options.
- Implement user authentication for secure access.
- Optimize scraper performance with parallel processing.

---
## Disclaimer
This project is developed solely for educational and research purposes. It is not intended for production use, commercial applications, or activities that violate the terms of service or intellectual property rights of any third party. The authors do not guarantee the accuracy, completeness, or reliability of the code or its outputs.

Users are solely responsible for ensuring compliance with all applicable laws, regulations, and terms of service when utilizing this project. The authors explicitly disclaim any liability for improper use, including but not limited to scraping or extracting data from external sources without proper authorization.