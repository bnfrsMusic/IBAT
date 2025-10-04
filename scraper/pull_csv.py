import requests

# This files loads the csv files with all the  


def download_github_file(url, save_as):
    try:
        #Get request
        response = requests.get(url, timeout=10)
        #raise exception for bad status code
        response.raise_for_status()

        with open(save_as, 'wb') as f:
            f.write(response.content)
        
        print(f"Successfully downloaded file to: {save_as}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")

def save_dat_csv():
    file_url = "https://raw.githubusercontent.com/jgalazka/SB_publications/main/SB_publication_PMC.csv"

    # Define the name for the local file
    local_filename = "data/csv/SB_publication_PMC.csv"

    download_github_file(file_url, local_filename)