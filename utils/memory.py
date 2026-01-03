
import os
import json
import time
import numpy as np
import warnings
# Suppress the deprecation warning
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
import google.generativeai as genai
import ollama
from ollama import Client as OllamaClient
from dotenv import load_dotenv

load_dotenv()

MEMORY_FILE = "memory_store.json"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

# Configuration
MAX_MEMORIES = 200
SIMILARITY_THRESHOLD = 0.65 # Minimum similarity to be considered relevant

class MemorySystem:
    def __init__(self, memory_file=MEMORY_FILE):
        self.memory_file = memory_file
        self.memories = self._load_memory()
        
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.embedding_provider = "gemini"
        else:
            self.embedding_provider = "ollama"

    def _load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except json.JSONDecodeError:
                return []
        return []

    def _save_memory(self):
        # Prune if too large
        if len(self.memories) > MAX_MEMORIES:
            # Keep the most recent ones
            self.memories = self.memories[-MAX_MEMORIES:]
            
        with open(self.memory_file, 'w') as f:
            json.dump(self.memories, f, indent=4)

    def _get_embedding_gemini(self, text):
        try:
            # text-embedding-004 is current standard, embedding-001 is legacy but stable
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception:
            try:
                 # Fallback
                result = genai.embed_content(
                    model="models/embedding-001",
                    content=text
                )
                return result['embedding']
            except Exception as e:
                print(f"[Memory] Gemini Embedding failed: {e}")
                return None

    def _get_embedding_ollama(self, text):
        if getattr(self, "embedding_disabled", False):
            return None
            
        try:
            model = os.getenv("OLLAMA_MODEL", "llama3.2")
            # Use the simple python library call which maps to /api/embeddings correctly
            response = ollama.embeddings(model=model, prompt=text)
            return response.get('embedding')
        except Exception as e:
            # Fallback/Error Handling: Disable if endpoint missing (404) to avoid spam
            if "404" in str(e):
                print(f"[System] Local embedding not supported key ('{model}'). Memory features disabled.")
                self.embedding_disabled = True
            else:
                print(f"[Memory] Ollama Embedding failed: {e}")
            return None

    def _get_embedding(self, text):
        if self.embedding_provider == "gemini":
            try:
                emb = self._get_embedding_gemini(text)
                if emb: return emb
            except Exception as e:
                print(f"[Memory] Unexpected Gemini error: {e}. Falling back...")
            
            # Fallback to ollama if gemini fails or returns None
            return self._get_embedding_ollama(text)
        else:
            return self._get_embedding_ollama(text)

    def add_memory(self, prompt, response, metadata=None):
        if not prompt or not response:
            return

        # Combine text for embedding
        text_to_embed = f"Request: {prompt}\nResult: {response}"
        embedding = self._get_embedding(text_to_embed)

        if embedding:
            memory_item = {
                "id": str(time.time()),
                "prompt": prompt,
                "response": response,
                "embedding": embedding,
                "metadata": metadata or {},
                "timestamp": time.time()
            }
            self.memories.append(memory_item)
            self._save_memory()

    def retrieve_context(self, query, top_k=2):
        """
        Retrieves relevant past interactions based on query similarity.
        Returns a formatted string of context.
        """
        if not self.memories:
            return ""

        query_embedding = self._get_embedding(query)
        if not query_embedding:
            return ""

        query_vec = np.array(query_embedding)
        
        scores = []
        for mem in self.memories:
            if 'embedding' not in mem: continue
            mem_vec = np.array(mem['embedding'])
            
            # Use dot product / cosine similarity
            # Use dot product / cosine similarity
            # Ensure dimensions match (Gemini vs Ollama embeddings might differ if mixed)
            if mem_vec.shape != query_vec.shape:
                # print(f"[Memory] Dimension mismatch: Query {query_vec.shape} vs Mem {mem_vec.shape}")
                continue

            norm_q = np.linalg.norm(query_vec)
            norm_m = np.linalg.norm(mem_vec)
            
            if norm_q == 0 or norm_m == 0:
                similarity = 0
            else:
                similarity = np.dot(query_vec, mem_vec) / (norm_q * norm_m)
            
            scores.append((similarity, mem))

        # Sort by similarity descending
        scores.sort(key=lambda x: x[0], reverse=True)
        top_results = scores[:top_k]

        relevant_memories = []
        for score, mem in top_results:
            if score >= 0.4: # Lowered threshold from 0.65 to 0.4 for better recall
                # Truncate very long responses for context window sanity
                short_response = mem['response']
                if len(short_response) > 500:
                    short_response = short_response[:500] + "...(truncated)"
                
                relevant_memories.append(f"PAST INTERACTION (Score: {score:.2f}):\nQ: {mem['prompt']}\nA: {short_response}")

        if not relevant_memories:
            # print("[Memory] No relevant context found.")
            return ""
            
        print(f"  [Memory] Retrieved {len(relevant_memories)} context vectors (Top Score: {top_results[0][0]:.2f})")
        return "\n\n".join(relevant_memories)
