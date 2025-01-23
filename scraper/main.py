import multiprocessing
import time
from datetime import timedelta

from LixkedIx import run_LixkedIx_scraper
from PrxcujPX import run_PrxcujPX_scraper
from JJxT import run_JJXT_scraper
from scraper.BullDxgJxb import run_BullDxgJxb_scraper
from scraper.NxFluffJxbs import run_NxFluffJxbs_scraper
from scraper.shared import all_tech


if __name__ == "__main__":
    start_time = time.monotonic()

    updateInCaseOfExistingInDB = input("Do You want to update existing records (y/n)?").lower().strip() == 'y'

    updateOpenAIApiPart = input("Do You want to update part based on OpenAI (y/n)?").lower().strip() == 'y'

    runMultiprocessing = input("Do You want to run using multiprocessing (y/n)?").lower().strip() == 'y'

    if(runMultiprocessing):
        # Definiujemy procesy dla różnych funkcji
        procesy = [
            multiprocessing.Process(target=run_LixkedIx_scraper, args=(updateInCaseOfExistingInDB, updateOpenAIApiPart,)),
            multiprocessing.Process(target=run_PrxcujPX_scraper, args=(updateInCaseOfExistingInDB, updateOpenAIApiPart,)),
            multiprocessing.Process(target=run_JJXT_scraper, args=(updateInCaseOfExistingInDB, updateOpenAIApiPart,)),
            multiprocessing.Process(target=run_NxFluffJxbs_scraper, args=(updateInCaseOfExistingInDB, updateOpenAIApiPart,)),
            multiprocessing.Process(target=run_BullDxgJxb_scraper, args=(updateInCaseOfExistingInDB, updateOpenAIApiPart,))
        ]

        # Uruchamiamy procesy
        for proces in procesy:
            proces.start()

        # Czekamy na zakończenie wszystkich procesów
        for proces in procesy:
            proces.join()
    else:
        run_LixkedIx_scraper(updateInCaseOfExistingInDB=updateInCaseOfExistingInDB, updateOpenAIApiPart=updateOpenAIApiPart)
        run_PrxcujPX_scraper(updateInCaseOfExistingInDB=updateInCaseOfExistingInDB, updateOpenAIApiPart=updateOpenAIApiPart)
        run_JJXT_scraper(updateInCaseOfExistingInDB=updateInCaseOfExistingInDB, updateOpenAIApiPart=updateOpenAIApiPart)
        run_NxFluffJxbs_scraper(updateInCaseOfExistingInDB=updateInCaseOfExistingInDB, updateOpenAIApiPart=updateOpenAIApiPart)
        run_BullDxgJxb_scraper(updateInCaseOfExistingInDB=updateInCaseOfExistingInDB, updateOpenAIApiPart=updateOpenAIApiPart)

    print("Wszystkie procesy zakończone.")
    print("ALL TECH:")
    print(all_tech)

    end_time = time.monotonic()
    print(f"total time: {timedelta(seconds=end_time - start_time)}")