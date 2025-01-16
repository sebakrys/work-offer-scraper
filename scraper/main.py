import time
from datetime import timedelta

from LixkedIx import run_LixkedIx_scraper
from PrxcujPX import run_PrxcujPX_scraper
from JJxT import run_JJXT_scraper
from scraper.BullDxgJxb import run_BullDxgJxb_scraper
from scraper.NxFluffJxbs import run_NxFluffJxbs_scraper
from scraper.shared import all_tech

start_time = time.monotonic()

updateInCaseOfExistingInDB = input("Do You want to update existing records (y/n)?").lower().strip() == 'y'

updateOpenAIApiPart = input("Do You want to update part based on OpenAI (y/n)?").lower().strip() == 'y'


#run_LixkedIx_scraper(updateInCaseOfExistingInDB=updateInCaseOfExistingInDB, updateOpenAIApiPart=updateOpenAIApiPart)

#run_PrxcujPX_scraper(updateInCaseOfExistingInDB=updateInCaseOfExistingInDB, updateOpenAIApiPart=updateOpenAIApiPart)

#run_JJXT_scraper(updateInCaseOfExistingInDB=updateInCaseOfExistingInDB, updateOpenAIApiPart=updateOpenAIApiPart)

run_NxFluffJxbs_scraper(updateInCaseOfExistingInDB=updateInCaseOfExistingInDB, updateOpenAIApiPart=updateOpenAIApiPart)

#run_BullDxgJxb_scraper(updateInCaseOfExistingInDB=updateInCaseOfExistingInDB, updateOpenAIApiPart=updateOpenAIApiPart)

print("ALL TECH:")
print(all_tech)

end_time = time.monotonic()
print(f"total time: {timedelta(seconds=end_time - start_time)}")