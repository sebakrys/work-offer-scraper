from LinkedIn import run_LinkedIn_scraper
from PracujPL import run_PracujPL_scraper, all_tech


disable_OpenAI = not (input("Do you want to use OpenAI API (y/n)?").lower().strip() == 'y')
updateExperienceYears = input("Do you want to update Experience Years(y/n)?").lower().strip() == 'y'
updateInCaseOfExistingInDB = True

#run_LinkedIn_scraper(disable_OpenAI=disable_OpenAI, updateExperienceYears=updateExperienceYears, updateInCaseOfExistingInDB=updateInCaseOfExistingInDB)

run_PracujPL_scraper(disable_OpenAI=disable_OpenAI, updateExperienceYears=updateExperienceYears, updateInCaseOfExistingInDB=updateInCaseOfExistingInDB)

