import sys
import os
from dotenv import load_dotenv

# Import stages
from stages.stage1_topic import stage1_topic_decomposition
from stages.stage2_discovery import stage2_document_discovery
from stages.stage3_analysis import stage3_document_analysis
from stages.stage4_scoring import stage4_academic_scoring
from stages.stage5_filtering import stage5_selection_filtering
from stages.stage6_synthesis import stage6_research_synthesis
from stages.stage7_generation import stage7_paper_generation

from stages.stage8_review import stage8_review_paper

def main():
    load_dotenv()
    
    # Check for API keys or Offline Mode
    # ... (existing checks implicitly fine)

    # Input
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = input("Enter Research Topic: ")
        
    if not topic:
        print("Topic required.")
        return

    # Pipeline Execution
    
    # Stage 1
    decomposition = stage1_topic_decomposition(topic)
    if not decomposition: return

    # Stage 2
    raw_docs = stage2_document_discovery(decomposition)
    if not raw_docs:
        print("No documents found.")
        return

    # Stage 3
    analyzed_docs = stage3_document_analysis(raw_docs)
    
    # Stage 4
    scored_docs = stage4_academic_scoring(analyzed_docs, topic)
    
    # Stage 5
    knowledge_base = stage5_selection_filtering(scored_docs)
    
    if not knowledge_base:
        print("No high-quality documents retained necessary to proceed.")
        return

    # Stage 6
    synthesis = stage6_research_synthesis(knowledge_base, topic)
    if not synthesis: return

    # Stage 7 & 8 Loop
    loop_count = 0
    max_loops = 5 # Increased retry limit for quality assurance
    feedback = ""
    
    while loop_count < max_loops:
        final_paper = stage7_paper_generation(synthesis, knowledge_base, topic, feedback=feedback)
        
        # Review
        review = stage8_review_paper(final_paper, topic)
        score = review.get('score', 0)
        
        if score >= 7:
            print(f"Paper accepted with score {score}.")
            break
        else:
            print(f"Paper rejected (Score {score}). Improving...")
            feedback = review.get('critique', 'General improvements needed.')
            loop_count += 1
    
    if loop_count >= max_loops:
        print("Max revisions reached. Saving current best effort.")
    
    # Output
    filename = f"{topic.replace(' ', '_').lower()}_paper.md"
    with open(filename, "w") as f:
        f.write(final_paper)
        
    print(f"\nSUCCESS. Paper generated and saved to {filename}")
    print("\nFINAL OUTPUT:\n")
    print(final_paper)

if __name__ == "__main__":
    main()
