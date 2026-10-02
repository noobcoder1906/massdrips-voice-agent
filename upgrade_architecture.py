import os
import json

# 1. RAG ENGINE
rag_code = """
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
            return "DYNAMIC STORE KNOWLEDGE:\\n" + "\\n".join(results)
        return ""

rag = RAGEngine()
"""

os.makedirs(r"d:\massdrips-voice-agent\backend\agent", exist_ok=True)
with open(r"d:\massdrips-voice-agent\backend\agent\rag_engine.py", "w", encoding="utf-8") as f:
    f.write(rag_code)

# 2. Update smart.py to use RAG
smart_path = r"d:\massdrips-voice-agent\backend\routes\smart.py"
with open(smart_path, "r", encoding="utf-8") as f:
    smart_content = f.read()

rag_import = "\nfrom backend.agent.rag_engine import rag\n"
if "rag_engine" not in smart_content:
    smart_content = smart_content.replace("from backend.agent.laya_router import laya_engine", "from backend.agent.laya_router import laya_engine" + rag_import)

# Inject RAG into system prompt for /fast-turn
rag_inject_target = """    system_prompt = build_system_prompt(tenant_config=tenant_config, lead_info=lead_info)"""
rag_inject_new = """    system_prompt = build_system_prompt(tenant_config=tenant_config, lead_info=lead_info)
    rag_context = rag.retrieve(user_text)
    if rag_context:
        system_prompt += f"\\n\\n{rag_context}"
"""
if "rag.retrieve" not in smart_content:
    smart_content = smart_content.replace(rag_inject_target, rag_inject_new)

with open(smart_path, "w", encoding="utf-8") as f:
    f.write(smart_content)

# 3. Update LiveCallModal.tsx for Barge-in
modal_path = r"d:\massdrips-voice-agent\voxsales-app\src\components\LiveCallModal.tsx"
with open(modal_path, "r", encoding="utf-8") as f:
    modal_content = f.read()

# Change onresult to support barge-in
old_onresult = """      recognition.onresult = (event: any) => {
        const text = event.results[0][0].transcript;
        if (text.trim()) {
          handleUserSpeech(text);
        }
      };"""

new_onresult = """      recognition.onresult = (event: any) => {
        const text = event.results[0][0].transcript;
        if (text.trim()) {
          // BARGE-IN: If AI is speaking, interrupt it!
          if (isAgentSpeakingRef.current && audioPlayerRef.current) {
            audioPlayerRef.current.pause();
            audioPlayerRef.current.currentTime = 0;
            isAgentSpeakingRef.current = false;
            setIsAgentSpeaking(false);
            console.log("BARGE-IN DETECTED! Interrupted AI.");
          }
          handleUserSpeech(text);
        }
      };"""

if "BARGE-IN" not in modal_content:
    modal_content = modal_content.replace(old_onresult, new_onresult)

# Make sure startListening() doesn't get blocked by isAgentSpeakingRef for true duplex
old_start = """  const startListening = () => {
    if (callState !== 'connected' || isAgentSpeakingRef.current || isProcessingRef.current) return;
    try {
      setIsListening(true);
      recognitionRef.current?.start();
    } catch(e) {}
  };"""

new_start = """  const startListening = () => {
    if (callState !== 'connected' || isProcessingRef.current) return;
    try {
      setIsListening(true);
      recognitionRef.current?.start();
    } catch(e) {}
  };"""

if "isAgentSpeakingRef.current || isProcessingRef.current" in modal_content:
    modal_content = modal_content.replace(old_start, new_start)

# Make sure onend restarts recognition even if agent is speaking (listening for barge-in)
old_onend = """        if (callState === 'connected' && !isAgentSpeakingRef.current && !isProcessingRef.current) {"""
new_onend = """        if (callState === 'connected' && !isProcessingRef.current) {"""
if old_onend in modal_content:
    modal_content = modal_content.replace(old_onend, new_onend)

with open(modal_path, "w", encoding="utf-8") as f:
    f.write(modal_content)

print("10/10 Architecture Upgrades (RAG + Barge-in) Applied!")
