import json
import logging
from utils.llm import query_stage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_plagiarism_and_novelty(text: str) -> dict:
    """
    Analyzes the text for AI-likelihood/novelty score and paraphrases it for enhanced results.
    Doesn't require external references - relies on LLM's vast training data to detect clichés, common AI phrasing, and generic structures.
    """
    if not text:
        return {"similarity_score": 0.0, "novelty_score": 10.0, "paraphrased_text": "", "paraphrase_detected": False, "engine": "error-fallback"}

    prompt = f"""
You are an expert AI originality detector and specialized editor. 
Analyze the following text.
1. Determine a Novelty Score out of 10. (10 means highly original and creative, 0 means entirely generic AI cliches or copied-sounding text).
2. Predict an AI/Similarity Score (0.0 to 1.0) representing the likelihood this was AI-generated, generic, or heavily unoriginal. (1.0 = highly generic/plagiarized).
3. Paraphrase and enhance the text to make it completely human-sounding, highly original, engaging, and flow logically without losing the core meaning.

Provide your response STRICTLY as a valid JSON object with NO markdown formatting, NO backticks, and NO additional text:
{{
    "similarity_score": 0.00,
    "novelty_score": 0.0,
    "paraphrased_text": "string containing the enhanced text"
}}

TEXT TO ANALYZE:
{text}
"""
    try:
        response = query_stage("analysis", prompt)
        
        # Clean response string to parse JSON safely if LLM returns markdown formatting
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
             response = response[3:]
        if response.endswith("```"):
             response = response[:-3]
        response = response.strip()
        
        result = json.loads(response)
        
        similarity_score = float(result.get("similarity_score", 0.0))
        
        return {
            "similarity_score": similarity_score,
            "novelty_score": float(result.get("novelty_score", 10.0)),
            "paraphrased_text": str(result.get("paraphrased_text", "")),
            "paraphrase_detected": similarity_score > 0.6,
            "engine": "llm-enhancer"
        }
    except Exception as e:
        logger.error(f"Error during LLM analysis: {e}")
        return {
            "similarity_score": 0.0,
            "novelty_score": 0.0,
            "paraphrased_text": "Failed to enhance the text due to an error.",
            "paraphrase_detected": False,
            "engine": "error-fallback"
        }
