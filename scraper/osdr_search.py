import requests
import json
from typing import List, Dict, Optional

class NASAOSDRSearch:
    """Search NASA's Open Science Data Repository for studies."""
    
    def __init__(self):
        self.base_url = "https://osdr.nasa.gov/osdr/data/search"
        
    def search_studies(self, keyword: str, max_results: int = 10, 
                      data_source: str = "cgene") -> List[Dict]:
        """
        Search for studies by keyword in NASA OSDR.
        """
        try:
            # search parameters
            params = {
                'term': keyword,
                'from': 0,
                'size': max_results,
                'type': data_source
            }
            
            #API request
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            # Parse 
            data = response.json()
            
            # Extract relevant study information
            studies = []
            if 'hits' in data and 'hits' in data['hits']:
                for hit in data['hits']['hits']:
                    source = hit.get('_source', {})
                    study = {
                        'id': hit.get('_id'),
                        'accession': source.get('Accession', 'N/A'),
                        'title': source.get('Study Title', 'N/A'),
                        'description': source.get('Study Description', 'N/A'),
                        'organism': source.get('organism', []),
                        'project_type': source.get('Project Type', 'N/A'),
                        'assay_type': source.get('Study Assay Technology Type', []),
                        'factor_name': source.get('Study Factor Name', []),
                        'managing_center': source.get('Managing NASA Center', 'N/A'),
                        'release_date': source.get('Study Public Release Date', 'N/A'),
                        'score': hit.get('_score', 0)
                    }
                    studies.append(study)
            
            return studies
            
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return []
    
    def search_with_filters(self, keyword: str = "", max_results: int = 10,
                           organism: str = None, assay_type: str = None,
                           project_type: str = None) -> List[Dict]:
        try:
            params = {
                'from': 0,
                'size': max_results,
                'type': 'cgene'
            }
            
            if keyword:
                params['term'] = keyword
            
            # Add filters using ffield and fvalue pairs
            if organism:
                params['ffield'] = 'organism'
                params['fvalue'] = organism
            
            if assay_type:
                if 'ffield' in params:
                    #Convert to lists
                    params['ffield'] = [params['ffield'], 'Study Assay Technology Type']
                    params['fvalue'] = [params['fvalue'], assay_type]
                else:
                    params['ffield'] = 'Study Assay Technology Type'
                    params['fvalue'] = assay_type
            
            if project_type:
                if 'ffield' in params:
                    if isinstance(params['ffield'], list):
                        params['ffield'].append('Project Type')
                        params['fvalue'].append(project_type)
                    else:
                        params['ffield'] = [params['ffield'], 'Project Type']
                        params['fvalue'] = [params['fvalue'], project_type]
                else:
                    params['ffield'] = 'Project Type'
                    params['fvalue'] = project_type
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            studies = []
            if 'hits' in data and 'hits' in data['hits']:
                for hit in data['hits']['hits']:
                    source = hit.get('_source', {})
                    study = {
                        'id': hit.get('_id'),
                        'accession': source.get('Accession', 'N/A'),
                        'title': source.get('Study Title', 'N/A'),
                        'description': source.get('Study Description', 'N/A'),
                        'organism': source.get('organism', []),
                        'project_type': source.get('Project Type', 'N/A'),
                        'assay_type': source.get('Study Assay Technology Type', []),
                        'factor_name': source.get('Study Factor Name', []),
                        'managing_center': source.get('Managing NASA Center', 'N/A'),
                        'release_date': source.get('Study Public Release Date', 'N/A'),
                        'score': hit.get('_score', 0)
                    }
                    studies.append(study)
            
            return studies
            
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return []


def test():
    searcher = NASAOSDRSearch()

    results = searcher.search_studies(keyword="mouse", max_results=10)

    for i, study in enumerate(results, 1):
        print(f"{i}. {study['title']}")
        print(f"   Accession: {study['accession']}")
        print(f"   Description: {study['description']}")
        print(f"   Organism: {study['organism']}")
        print(f"   Project Type: {study['project_type']}")
        print(f"   Assay Type: {study['assay_type']}")
        print(f"   Managing Center: {study['managing_center']}")
        print(f"   Release Date: {study['release_date']}")
        print(f"   Relevance Score: {study['score']}\n")
