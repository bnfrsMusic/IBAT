from rake_nltk import Rake
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Optional, Tuple
from scraper.ncbi_search import NCBISearch
from scraper.osdr_search import NASAOSDRSearch
import numpy as np
import execjs

class RAGProcessor:

    def __init__(self):
        nltk.download('stopwords')
        nltk.download('punkt_tab')
        self.ncbi = NCBISearch()
        self.osdr = NASAOSDRSearch()
        self.ncbi_queries: List[str] = []
        self.osdr_queries: List[str] = []
        
        # Conversation history tracking
        self.conversation_history: List[Dict[str, str]] = []
        self.last_keywords: List[str] = []
        self.last_topic: Optional[str] = None
        
    ##---------------------------Context Management---------------------------
    def _is_followup_question(self, current_prompt: str) -> bool:
        """Detect if current prompt is a follow-up question"""
        followup_indicators = [
            'what about', 'how about', 'and', 'also', 'additionally',
            'furthermore', 'more', 'tell me more', 'elaborate', 'explain',
            'why', 'how', 'when', 'where', 'can you', 'could you',
            'what if', 'suppose', 'in that case', 'regarding', 'about that'
        ]
        
        # Check for pronouns that reference previous context
        context_pronouns = ['it', 'this', 'that', 'these', 'those', 'they', 'them']
        
        prompt_lower = current_prompt.lower().strip()
        
        # Short questions are likely follow-ups
        if len(prompt_lower.split()) <= 5:
            return True
            
        # Check for follow-up indicators
        for indicator in followup_indicators:
            if prompt_lower.startswith(indicator):
                return True
                
        # Check for context pronouns
        words = prompt_lower.split()
        if any(word in context_pronouns for word in words[:3]):
            return True
            
        return False
    
    def _calculate_topic_similarity(self, current_prompt: str, threshold: float = 0.3) -> float:
        """Calculate similarity between current prompt and last topic"""
        if not self.last_topic:
            return 0.0
            
        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            vectors = vectorizer.fit_transform([self.last_topic, current_prompt])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return similarity
        except:
            return 0.0
    
    def _merge_context(self, current_prompt: str, context_window: int = 2) -> str:
        """Merge current prompt with relevant conversation history"""
        if not self.conversation_history:
            return current_prompt
            
        # Get last N exchanges from history
        recent_history = self.conversation_history[-context_window:]
        
        # Build context string
        context_parts = []
        for entry in recent_history:
            if entry.get('user'):
                context_parts.append(entry['user'])
                
        # Combine with current prompt
        if context_parts:
            merged = ' '.join(context_parts) + ' ' + current_prompt
            return merged
        
        return current_prompt
    
    def _should_use_context(self, current_prompt: str) -> Tuple[bool, str]:
        """Determine if context should be used and return appropriate prompt"""
        # If no history, use current prompt as-is
        if not self.conversation_history:
            return False, current_prompt
            
        is_followup = self._is_followup_question(current_prompt)
        similarity = self._calculate_topic_similarity(current_prompt)
        
        # Use context if it's a follow-up or similar topic
        if is_followup or similarity > 0.3:
            merged_prompt = self._merge_context(current_prompt)
            return True, merged_prompt
        
        # New topic - reset context
        return False, current_prompt
    
    def _update_conversation_history(self, user_prompt: str, keywords: List[str]):
        """Update conversation history with new interaction"""
        self.conversation_history.append({
            'user': user_prompt,
            'keywords': keywords,
            'timestamp': len(self.conversation_history)
        })
        
        # Keep only last 10 interactions to prevent unbounded growth
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        # Update tracking variables
        self.last_keywords = keywords
        self.last_topic = user_prompt
    
    def clear_context(self):
        """Clear conversation history - useful for new topics"""
        self.conversation_history = []
        self.last_keywords = []
        self.last_topic = None
        
    ##---------------------------Keyword Processing---------------------------
    def _text_extraction(self, User_Input: str) -> List[str]:
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
        return f"\nPossible Relevant Paper: {title}\n{section_name}: {section_value}\nContent: {abstract}\n"

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
        # try:
        # with open('frontend/scriptreport_server.js', 'wr') as f:
        #     js_code = f.read()

        # ctx = execjs.compile(js_code)

        # # Clear any old reports before starting
        # ctx.call('clearReports')

        print("NCBI Queries:")
        for query in self.ncbi_queries:
            print(f" - {query['title']}")
            # result = ctx.call('addReport', query['title'], query['link'], query['link'])
            # print(f"Result: {result}")
            print(f"link: {query['link']}")

        print("NASA OSDR Queries:")
        for query in self.osdr_queries:
            # result = ctx.call('addReport', query['title'], query['link'], query['link'])
            print(f" - {query['title']}")
        


        #----------------Format for RAG----------------
        rag_output = "This is an English Text, reply in English. Use relevant papers to answer the question. If question is not in papers, then mention that your answer is general knowledge and may be incorrect. Be as detailed as you can when referencing or summarizing papers. If salutations and such, answer politely.\n"
        for query in self.ncbi_queries:
            abstract = self.ncbi.get_section(url=query['link'], section="Abstract")
            results = self.ncbi.get_section(url=query['link'], section="Results")
            c = None
            if category:
                c = self.ncbi.get_section(url=query['link'], section=category)
            if abstract:
                rag_output += self._format(query['title'], abstract, category, c)
                rag_output += self._format(query['title'], results, category, c)

        return rag_output

    def search(self, prompt: str, force_new_topic: bool = False):
        """
        Main search function with context awareness
        
        Args:
            prompt: User's query
            force_new_topic: If True, ignores context and starts fresh
        """
        if force_new_topic:
            self.clear_context()
        
        # Determine if we should use conversation context
        use_context, processed_prompt = self._should_use_context(prompt)
        
        if use_context:
            print(f"[Context Mode] Detected follow-up question")
            print(f"[Context Mode] Merged prompt: {processed_prompt}")
            # Use previous keywords combined with new ones
            keywords = self._text_extraction(processed_prompt)
            
            # Optionally blend with last keywords for continuity
            if self.last_keywords:
                keywords = list(set(keywords + self.last_keywords[:3]))  # Add top 3 previous keywords
                print(f"[Context Mode] Blended keywords: {keywords[:5]}")
        else:
            print(f"[New Topic Mode] Processing as new query")
            keywords = self._text_extraction(prompt)
        
        print(f"[Keywords] Extracted: {keywords[:5] if len(keywords) > 5 else keywords}")
        
        # Update conversation history
        self._update_conversation_history(prompt, keywords)
        
        # Perform search
        r = self.query_search(keywords)
        
        # Return original prompt with RAG context
        # The LLM needs the original question, not the merged one
        final_output = f"{prompt}\n" + r
        print(f"[Search Complete] Total context length: {len(final_output)} chars")
        
        return final_output

    def get_ncbi_sources(self) -> List[Dict[str, str]]:
        """Returns a list of unique NCBI sources from the last query."""
        unique_sources = []
        seen_links = set()
        for item in self.ncbi_queries:
            if item['link'] not in seen_links:
                unique_sources.append({
                    "title": item['title'],
                    "source": item['link']
                })
                seen_links.add(item['link'])
        return unique_sources

# Example usage:
# r = RAGProcessor()
# 
# # First question
# print(r.search("What plants grow best in microgravity?"))
# 
# # Follow-up questions (will use context)
# print(r.search("What about their growth rate?"))
# print(r.search("How do they compare to Earth?"))
# 
# # New topic (will reset context)
# print(r.search("Tell me about radiation effects on astronauts"))
# 
# # Force new topic
# print(r.search("Back to plants", force_new_topic=True))