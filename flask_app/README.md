# Flask App

## Overview

The `flask_app` directory contains a Flask-based web application that provides an API and a front-end interface for managing and visualizing job offers stored in a PostgreSQL database.

## Features

- **API Endpoints**:
  - `/api/data`: Fetch all job offers in JSON format.
  - `/api/update_applied`: Update the `applied` status of a specific job offer.
- **Front-End**:
  - A table for browsing job offers with sorting and filtering capabilities.
  - Ability to copy required skills to the clipboard and mark offers as applied.

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database

### Setup

1. Navigate to the `flask_app` directory:
   ```bash
   cd flask_app
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file with the following variables:
   ```env
   DATABASE_URL=your_postgresql_connection_string
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Open your browser and navigate to `http://127.0.0.1:5000`.


## Technologies Used

- **Framework**: Flask
- **Database**: PostgreSQL
- **Front-End**: HTML, CSS, JavaScript (DataTables)

