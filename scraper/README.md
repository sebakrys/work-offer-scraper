
# Scraper

## Overview

The `scraper` directory contains scripts for collecting job offers from various online sources and storing them in a PostgreSQL database. It includes NLP-based analysis and optional integration with OpenAI GPT for enhanced data processing.

## Features

- **Supported Sources**:
  - LixkedIx
  - PrxcujPX
  - NxFluffJxbs
  - JJxT
  - BullDxgJxb
- **Extracted Data**:
  - Job title, organization, location, required skills, experience, job level, application URL, and more.
- **Enhancements**:
  - NLP-based skill extraction and job analysis.
  - OpenAI GPT integration for generating CV-ready skills sections and identifying experience requirements.

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database
- OpenAI API key (optional)

### Setup

1. Navigate to the `scraper` directory:
   ```bash
   cd scraper
   ```

2. Install dependencies:
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

4. Run the scraper:
   ```bash
   python main.py
   ```

5. Follow the prompts to configure scraping options.


## Technologies Used

- **Scraping**: Playwright, BeautifulSoup
- **Database**: PostgreSQL
- **NLP & AI**: spaCy, OpenAI GPT

## Future Improvements

- Enhance performance with parallel scraping.
- Improve error handling and logging.

---
## Disclaimer
This project is developed solely for educational and research purposes. It is not intended for production use, commercial applications, or activities that violate the terms of service or intellectual property rights of any third party. The authors do not guarantee the accuracy, completeness, or reliability of the code or its outputs.

Users are solely responsible for ensuring compliance with all applicable laws, regulations, and terms of service when utilizing this project. The authors explicitly disclaim any liability for improper use, including but not limited to scraping or extracting data from external sources without proper authorization.

