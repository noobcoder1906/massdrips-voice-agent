
import os
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class RAGEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.documents = []
        self.doc_texts = []
        self.tfidf_matrix = None
        self._load_knowledge()

    def _load_knowledge(self):
        store_file = os.path.join(os.path.dirname(__file__), "..", "services", "scraped_site_data.json")
        if not os.path.exists(store_file):
            return
            
        with open(store_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Create documents from collections
        for col in data.get("collections", []):
            text = f"Collection: {col.get('name')}. Details: {col.get('desc')}. Starts at {col.get('startingPrice')}"
            self.documents.append(text)
            self.doc_texts.append(text)
            
        # Create documents from products
        for prod in data.get("products", []):
            text = f"Product: {prod.get('name')}, Price: {prod.get('price')}, Color: {prod.get('color')}, Fabric: {prod.get('gsm')}, Category: {prod.get('category')}. Badge: {prod.get('badge')}"
            self.documents.append(text)
            self.doc_texts.append(text)
            
        # Add store policies
        policy = f"Shipping: {data.get('shipping')}. Payment: {data.get('payment')}. Discount: {data.get('discount_code')}. Fabric quality: {data.get('fabric')}"
        self.documents.append(policy)
        self.doc_texts.append(policy)
        
        if self.doc_texts:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.doc_texts)

    def retrieve(self, query: str, top_k: int = 3) -> str:
        if self.tfidf_matrix is None or not query.strip():
            return ""
            
        query_vec = self.vectorizer.transform([query])
        sim_scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        top_indices = np.argsort(sim_scores)[-top_k:][::-1]
        
        # Only return matches with a score > 0.1
        results = []
        for idx in top_indices:
            if sim_scores[idx] > 0.1:
                results.append(self.doc_texts[idx])
                
        if results:
            return "DYNAMIC STORE KNOWLEDGE:\n" + "\n".join(results)
        return ""

rag = RAGEngine()
