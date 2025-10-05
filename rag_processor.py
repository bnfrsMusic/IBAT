from rake_nltk import Rake
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from typing import List, Dict, Optional
from scraper.ncbi_search import NCBISearch
from scraper.osdr_search import NASAOSDRSearch


class RAGProcessor:

    def __init__(self):
        nltk.download('stopwords')
        nltk.download('punkt_tab')
        self.ncbi = NCBISearch()
        self.osdr = NASAOSDRSearch()
        self.ncbi_queries: List[str] = []
        self.osdr_queries: List[str] = []
    ##---------------------------Keyword Processing---------------------------
    def _text_extraction(self, User_Input:str) -> List[str]:
        r = Rake()
        r.extract_keywords_from_text(User_Input)
        return r.get_ranked_phrases()

    def _calculate_term_frequency(self, s: str):
        corpus = [s]
        vectorizer = CountVectorizer(stop_words='english')
        X = vectorizer.fit_transform(corpus)
        words = vectorizer.get_feature_names_out()
        if not words.any():
            return {}
        word_counts = X.toarray()[0]
        total_words = sum(word_counts)

        if total_words == 0:
            return {}
        term_frequencies = {word: count / total_words for word, count in zip(words, word_counts)}
        return term_frequencies

    def keyword_processor(self, inp: str):
        input_lower = inp.lower()
        all_word_tfs = self._calculate_term_frequency(input_lower)
        extracted_phrases = self._text_extraction(inp)
        phrase_scores = {}

        for phrase in extracted_phrases:
            score = 0
            words_in_phrase = phrase.lower().split()
            for word in words_in_phrase:
                score += all_word_tfs.get(word, 0)
            phrase_scores[phrase] = score
        
        return dict(sorted(phrase_scores.items(), key=lambda item: item[1], reverse=True))

    # maps input keywords to specific categories
    def keyword_mapper(input_str):
        keyword_map = {
            "results": ["result", "outcome", "product", "finding", "conclusion", "output", "effect", "consequence", "impact", "repercussion"],
            "method": ["method", "material", "approach", "technique", "how to", "procedure", "process", "way to", "mean"],
            "data": ["data", "information", "fact", "graph", "statistic", "detail", "evidence", "record", "figure", "table", "chart", "dataset", "measurement", "observation", "sample", "survey"],
            "analysis": ["analyze", "study", "examine", "evaluate", "investigate", "scrutinize", "review", "assess", "interpret", "breakdown", "inspect", "explore", "diagnose", "inspect"],
        }
        input_str = input_str.lower().strip()

        for keyword, synonyms in keyword_map.items():
            if input_str in synonyms:
                return keyword
            
        return None

    def _format(self, title, abstract, section_name, section_value) -> str:
        return f"Possible Relevant Paper: {title}\n{section_name}: {section_value}\nContent: {abstract}\n\n"

    ##---------------------------Query Search---------------------------
    def query_search(self, keywords: List[str], category: Optional[str] = None):
        
        #----------------NCBI Search----------------
        q = self.ncbi.search(keywords=keywords, csv_path="data\csv\SB_publication_PMC.csv", max_results=10)
        #queries with the highest match scores
        if q:
            max_score = max(item['match_score'] for item in q)
            self.ncbi_queries = [item for item in q if item['match_score'] == max_score]
        else:
            self.ncbi_queries = []
        
        #----------------NASA OSDR Search----------------
        for i in range(len(keywords)):
            o_q = self.osdr.search_studies(keyword=keywords[i], max_results=2)
            if o_q:
                max_o_score = max(item['score'] for item in o_q)
                top_o_queries = [item for item in o_q if item['score'] == max_o_score]
                self.osdr_queries.extend(top_o_queries)
        
        #----------------Print Queries----------------
    
        # print("NCBI Queries:")
        # for query in self.ncbi_queries:
        #     print(f" - {query['title']} (Score: {query['match_score']})")
        #     print(f"link: {query['link']}")
        #     # print(self.ncbi.get_section(url =query['link'], section="Abstract"))

        # print("NASA OSDR Queries:")
        # for query in self.osdr_queries:
        #     print(f" - {query['title']} (Score: {query['score']})")

        #----------------Format for RAG----------------
        rag_output = ""
        for query in self.ncbi_queries:
            abstract = self.ncbi.get_section(url=query['link'], section="Abstract")
            c = None
            if category:
                c = self.ncbi.get_section(url=query['link'], section=category)
            if abstract:
                rag_output += self._format(query['title'], abstract, category, c)

        return rag_output



    def search(self, prompt: str):
        keywords = self._text_extraction(prompt)
        r = self.query_search(keywords)
        return f"{prompt}\n" + r

r = RAGProcessor()
print(r.search("I want to know what plants grow the best in microgravity environment"))