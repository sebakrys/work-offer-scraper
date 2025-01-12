from LixkedIx import run_LinkedIn_scraper
from PrxcujPX import run_PracujPL_scraper, all_tech


disable_OpenAI = not (input("Do you want to use OpenAI API (y/n)?").lower().strip() == 'y')#todo to remove - but with caution
updateExperienceYears = input("Do you want to update Experience Years(y/n)?").lower().strip() == 'y'
updateInCaseOfExistingInDB = True

updateOpenAIApiPart = True # TODO dodac aby oszczedzac OPEN API api, jesli jest false to zostawic to co jest w bazie


run_LinkedIn_scraper(disable_OpenAI=disable_OpenAI, updateExperienceYears=updateExperienceYears, updateInCaseOfExistingInDB=updateInCaseOfExistingInDB)

run_PracujPL_scraper(disable_OpenAI=disable_OpenAI, updateExperienceYears=updateExperienceYears, updateInCaseOfExistingInDB=updateInCaseOfExistingInDB)

