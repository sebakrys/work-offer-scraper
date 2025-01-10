from flask import Flask, jsonify, render_template, request
from sqlalchemy.orm import Session

from scraper.database import JobOfferDB, save_job_offer_to_db, init_db, SessionLocal

app = Flask(__name__)

@app.route('/api/data', methods=['GET'])
def get_data():
    # Pobranie danych z bazy
    session = SessionLocal()
    try:
        offers = session.query(JobOfferDB).all()
        data = [
            {
                "id": offer.id,
                "applied": offer.applied,
                "url": offer.url,
                "date": offer.date.isoformat() if offer.date else None,
                "title": offer.title,
                "skill_deficiencies": offer.skill_deficiencies,
                "skill_percentage": offer.skill_percentage,
                "experience_years": offer.experience_years,
                "organization": offer.organization,
                "location": offer.location,
                "job_level": offer.job_level,
                "apply_url": offer.apply_url
            }
            for offer in offers
        ]
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True)





# Strona główna
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/update_applied', methods=['POST'])
def update_applied():
    """
    Aktualizuje pole 'applied' w bazie danych.
    """
    session: Session = SessionLocal()
    data = request.json
    job_id = data.get('id')
    applied = data.get('applied')

    if job_id is None or applied is None:
        return jsonify({"error": "Invalid input"}), 400

    try:
        job_offer = session.query(JobOfferDB).filter(JobOfferDB.id == job_id).first()
        if not job_offer:
            return jsonify({"error": "Job offer not found"}), 404

        job_offer.applied = applied
        session.commit()
        return jsonify({"message": "Applied status updated successfully!"})
    except Exception as e:
        session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True)
