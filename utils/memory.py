import os
import json
import time
import networkx as nx
import logging

logger = logging.getLogger(__name__)

MEMORY_FILE = "knowledge_graph.json"

class KnowledgeGraphMemory:
    def __init__(self, memory_file=MEMORY_FILE):
        self.memory_file = memory_file
        self.graph = nx.DiGraph()
        self._load_memory()
        
    def _load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    self.graph = nx.node_link_graph(data)
            except Exception as e:
                logger.error(f"Failed to load memory graph: {e}")
                self.graph = nx.DiGraph()

    def _save_memory(self):
        try:
            data = nx.node_link_data(self.graph)
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save memory graph: {e}")

    def _extract_triplets(self, text):
        from utils.llm import query_stage  # Local import to avoid circular dependency
        
        prompt = f"""
You are an expert NLP knowledge graph extractor.
Extract key entities, their relationships, and timelines/context from the following text.
Return the result strictly as a valid JSON list of objects. Each object must have exactly these keys:
"subject": string (the source entity, keep it short),
"predicate": string (the relationship or action),
"object": string (the target entity, keep it short),
"context": string (brief explanation or timeline info if any)

Return ONLY valid JSON logic. No markdown backticks.

TEXT:
{text}
"""
        try:
            # Route to a fast reasoning model
            response = str(query_stage("scoring", prompt, skip_memory=True)).strip()
            
            # Clean JSON formatting
            if response.startswith("```json"): response = response[7:]
            if response.startswith("```"): response = response[3:]
            if response.endswith("```"): response = response[:-3]
            response = response.strip()

            triplets = json.loads(response)
            if isinstance(triplets, list):
                return [t for t in triplets if isinstance(t, dict) and 'subject' in t and 'predicate' in t and 'object' in t]
            return []
        except Exception as e:
            logger.error(f"Graph Extractor Parsing failed: {e}")
            return []

    def add_memory(self, prompt, response, metadata=None):
        if not prompt or not response:
            return

        text_to_analyze = f"Context/Prompt: {prompt}\nResponse: {response}"
        triplets = self._extract_triplets(text_to_analyze)
        
        timestamp = time.time()
        added_count = 0
        
        for t in triplets:
            subj = str(t['subject']).strip().lower()
            pred = str(t['predicate']).strip().lower()
            obj = str(t['object']).strip().lower()
            ctx = str(t.get('context', ''))
            
            if not subj or not obj or not pred: continue
            if len(subj) > 50 or len(obj) > 50: continue # Skip if bad extraction
            
            # Add nodes
            if not self.graph.has_node(subj):
                self.graph.add_node(subj, type="entity")
            if not self.graph.has_node(obj):
                self.graph.add_node(obj, type="entity")
                
            # Add edge
            self.graph.add_edge(subj, obj, relation=pred, context=ctx, timestamp=timestamp)
            added_count += 1
            
        if added_count > 0:
            print(f"  [Knowledge Graph Builder] Extracted {added_count} entity relationships. The system accumulates structured knowledge, not just text.")
            self._save_memory()

    def retrieve_context(self, query, depth=2):
        if len(self.graph.nodes) == 0:
            return ""
            
        query_lower = query.lower()
        
        # Simple entity matching: find node names that appear in the query
        active_nodes = [n for n in self.graph.nodes if n in query_lower and len(n) > 3]
        
        # Fallback: if no direct match, look for word overlaps
        if not active_nodes:
            query_words = set(query_lower.split())
            for n in self.graph.nodes:
                if len(set(n.split()).intersection(query_words)) > 0:
                    active_nodes.append(n)
        
        if not active_nodes:
            return ""
            
        # Expand sub-graph up to N layers deep
        subgraph_nodes = set(active_nodes)
        for d in range(depth):
            current_layer = list(subgraph_nodes)
            for n in current_layer:
                subgraph_nodes.update(self.graph.predecessors(n))
                subgraph_nodes.update(self.graph.successors(n))
                
        subgraph = self.graph.subgraph(subgraph_nodes)
        
        edges = list(subgraph.edges(data=True))
        if len(edges) == 0:
            return ""
            
        # Sort by timestamp descending (newest first) to keep context relevant
        edges.sort(key=lambda x: x[2].get('timestamp', 0), reverse=True)
        # Cap at top 15 relationships to prevent token explosion
        edges = edges[:15]
            
        context_lines = []
        context_lines.append(f"KNOWLEDGE GRAPH MEMORY (Cross-Topic Entity Relations):")
        for u, v, data in edges:
            rel = data.get('relation', 'related to')
            ctx = data.get('context', '')
            
            line = f"- [{u}] <{rel}> [{v}]"
            if ctx: line += f" | Context: {ctx}"
            context_lines.append(line)
            
        print(f"  [Memory] Injected Knowledge Graph Context: {len(edges)} structured relationships linked to '{active_nodes[0]}'.")
        return "\n".join(context_lines)

# Export for backward compatibility with `utils/llm.py`
MemorySystem = KnowledgeGraphMemory
