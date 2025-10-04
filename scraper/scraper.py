import requests


OSD_STUDY_IDs, CURRENT_PAGE_NUMBER, RESULTS_PER_PAGE, ALL_FILES = 0
BASE_URL = f"https://osdr.nasa.gov/osdr/data/osd/files/{OSD_STUDY_IDs}/?page={CURRENT_PAGE_NUMBER}&size={RESULTS_PER_PAGE}?all_files={ALL_FILES} "

