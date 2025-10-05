import requests
import re
import xml.etree.ElementTree as ET


class NCBISearch:
    def __init__(self, email=None, api_key=None):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.email = email
        self.api_key = api_key

    def _extract_pmcid_number(self, url: str) -> str:
        """Extract numeric part of PMCID from URL"""
        match = re.search(r"PMC(\d+)", url)
        if not match:
            raise ValueError(f"Could not extract PMCID from URL: {url}")
        return match.group(1)

    def get_info(self, url: str) -> dict:
        """Fetch metadata (title, authors, journal, etc.)"""
        pmcid_num = self._extract_pmcid_number(url)
        params = {"db": "pmc", "id": pmcid_num, "retmode": "json"}
        if self.api_key:
            params["api_key"] = self.api_key
        if self.email:
            params["email"] = self.email

        response = requests.get(f"{self.base_url}esummary.fcgi", params=params)
        response.raise_for_status()
        data = response.json()

        result_key = next(iter(data["result"].keys() - {"uids"}))
        result = data["result"][result_key]

        info = {
            "title": result.get("title"),
            "authors": [a.get("name") for a in result.get("authors", [])],
            "journal": result.get("fulljournalname"),
            "pubdate": result.get("pubdate"),
            "doi": next(
                (i["value"] for i in result.get("articleids", []) if i["idtype"] == "doi"),
                None,
            ),
            "pmcid": f"PMC{pmcid_num}",
        }
        return info

    def get_section(self, url: str, section="Abstract") -> str:
        """Fetch and return the best-matching section text from the paper."""

        pmcid_num = self._extract_pmcid_number(url)
        params = {"db": "pmc", "id": pmcid_num, "retmode": "xml"}
        if self.api_key:
            params["api_key"] = self.api_key

        response = requests.get(f"{self.base_url}efetch.fcgi", params=params)
        response.raise_for_status()

        root = ET.fromstring(response.text)
        
        # ----------Direct match----------
        sec_return = root.findall(f".//{section.lower()}//p")
        if sec_return:
            sec_text = "\n".join(p.text.strip() for p in sec_return if p.text)
            if sec_text:
                return sec_text

        # ----------fuzzy match----------
        target = section.lower()
        exact_match = None
        partial_match = None

        for sec in root.findall(".//sec"):
            title_elem = sec.find("title")
            if title_elem is not None and title_elem.text:
                title_text = title_elem.text.strip().lower()
                if title_text == target:  # exact match
                    exact_match = sec
                    break
                elif target in title_text and partial_match is None:
                    partial_match = sec  # first partial match

        best_match = exact_match or partial_match
        if not best_match:
            return f"No section found with heading matching or similar to '{section}'."

        paragraphs = best_match.findall(".//p")
        sec_text = "\n".join(p.text.strip() for p in paragraphs if p.text)
        return sec_text or f"No text found in section '{section}'."


    def search(self, keyword: str) -> str



def test():
    fetcher = NCBISearch()
    url = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4136787/"

    info = fetcher.get_info(url)
    results_text = fetcher.get_section(url, section = "Abstract")

    print("Info:", info)
    print("\Section:\n", results_text)
