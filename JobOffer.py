class JobOffer:
    def __init__(self, url, date, title, organization, organization_url, location,
                 description, language, job_level, apply_url, web_id, skill_percentage = 0.0,
                 requirements=None, detected_technologies=None, skill_deficiencies = None, experience_years=[]):
        self.url = url
        self.date = date
        self.title = title
        self.organization = organization
        self.organization_url = organization_url
        self.location = location
        self.description = description
        self.language = language
        self.job_level = job_level
        self.apply_url = apply_url
        self.web_id = web_id
        self.requirements = requirements or []
        self.detected_technologies = detected_technologies or {}
        self.skill_deficiencies = skill_deficiencies
        self.skill_percentage = skill_percentage
        self.experience_years = experience_years

    def __repr__(self):
        return (f"JobOffer(title={self.title}, organization={self.organization}, "
                f"umiejetnosci={self.skill_percentage}"
                f"url={self.url}, date={self.date}, location={self.location}, "
                f"language={self.language}, web_id={self.web_id}, date={self.date}, requirements={self.requirements}, detected_technologies={self.detected_technologies})")

    def to_dict(self):
        """Convert the object to a dictionary."""
        return self.__dict__
