from LixkedIx import run_LinkedIn_scraper
from PrxcujPX import run_PracujPL_scraper
from JJxT import run_JJIT_scraper
from scraper.shared import all_tech

updateInCaseOfExistingInDB = input("Do You want to update existing records (y/n)?").lower().strip() == 'y'

updateOpenAIApiPart = input("Do You want to update part based on OpenAI (y/n)?").lower().strip() == 'y'


run_LinkedIn_scraper(updateInCaseOfExistingInDB=updateInCaseOfExistingInDB, updateOpenAIApiPart=updateOpenAIApiPart)

run_PracujPL_scraper(updateInCaseOfExistingInDB=updateInCaseOfExistingInDB, updateOpenAIApiPart=updateOpenAIApiPart)

run_JJIT_scraper(updateInCaseOfExistingInDB=updateInCaseOfExistingInDB, updateOpenAIApiPart=updateOpenAIApiPart)


print("ALL TECH:")
print(all_tech)