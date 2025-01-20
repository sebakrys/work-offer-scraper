from flask import Flask, jsonify, render_template, request
from sqlalchemy.orm import Session

from scraper.database import JobOfferDB, save_job_offer_to_db, init_db, SessionLocal

app = Flask(__name__)

@app.route('/api/data/appliedn0', methods=['GET'])
def get_data_appliedn0():
    print("get_data_appliedn0")
    # Pobranie danych z bazy
    session = SessionLocal()
    try:
        appliedOffers = session.query(JobOfferDB).filter(JobOfferDB.applied==True).count()

        data = {"appliedN0": appliedOffers}

        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route('/api/data', methods=['GET'])
def get_data():
    # Pobranie danych z bazy
    session = SessionLocal()
    try:
        offers = session.query(JobOfferDB).filter(JobOfferDB.hidden==False, JobOfferDB.applied==False)
        data = [
            {
                "id": offer.id,
                "applied": offer.applied,
                "language": offer.language,
                "url": offer.url,
                "date": offer.date.isoformat() if offer.date else None,
                "title": offer.title,
                "skill_deficiencies": offer.skill_deficiencies,
                "skill_percentage": offer.skill_percentage,
                "skills_for_cv": offer.skills_for_cv,
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

@app.route('/api/update_hidden', methods=['POST'])
def update_hidden():
    """
    Aktualizuje pole 'applied' w bazie danych.
    """
    session: Session = SessionLocal()
    data = request.json
    job_id = data.get('id')
    hidden = data.get('hidden')

    if job_id is None or hidden is None:
        return jsonify({"error": "Invalid input"}), 400

    try:
        job_offer = session.query(JobOfferDB).filter(JobOfferDB.id == job_id).first()
        if not job_offer:
            return jsonify({"error": "Job offer not found"}), 404

        job_offer.hidden = hidden
        session.commit()
        return jsonify({"message": "Hidden status updated successfully!"})
    except Exception as e:
        session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally:
        session.close()


if __name__ == '__main__':
    app.run(debug=True)
