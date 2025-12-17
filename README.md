# Multi-Layer Research Agent 🔬📚

**An autonomous AI agent designed to generate high-quality, Scopus-standard academic research papers through a rigorous multi-stage pipeline.**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Status](https://img.shields.io/badge/status-active-success)

## 📖 Overview

The **Multi-Layer Research Agent** is a sophisticated system that emulates the workflow of a human researcher. Instead of a single LLM call, it orchestrates a specialized pipeline of agents to **decompose topics, search for real-world sources, analyze credentials, synthesize findings, and write professional academic papers**.

Key differentiator: It features a **Self-Correction Loop**. Stage 8 (Review) acts as a critical peer reviewer. If the generated paper does not meet academic standards (score < 7/10), it rejects the paper and sends constructive feedback back to Stage 7 for regeneration.

---

## 🚀 Key Features

*   **Multi-Stage Architecture**: Deconstructs the complexity of research into 8 manageable, specialized stages.
*   **Hybrid LLM Engine**:
    *   **Cloud Prioritized**: Uses **Gemini 1.5 Pro** and **Groq (Llama 3 70B)** for speed and high context.
    *   **Offline Fallback**: Fully capable of running completely offline using local models via Hugging Face Transformers (requires GPU).
*   **Real-Time Internet Research**: Integrates with **Google Programmable Search Engine** to find recognized academic sources.
*   **Academic Scoring System**: Automatically evaluates sources based on relevance, credibility, and citationworthiness.
*   **Auto-Iterative Improvement**: The agent crtiques its own work and improves it iteratively before final output.

---

## 🏗️ The Pipeline (8 Stages)

1.  **Topic Decomposition**: Breaks the user's prompt into key research questions and search queries.
2.  **Document Discovery**: Searches the web for PDFs, articles, and academic papers.
3.  **Analysis**: Reads contents, extracting key arguments, methodologies, and data.
4.  **Scoring**: Rates documents on a 0-10 academic scale; filters out low-quality/irrelevant noise.
5.  **Filtering & Selection**: Compiles the final "Knowledge Base" of top-tier references.
6.  **Synthesis**: Aggregates the knowledge base into a structured logical flow (outlining).
7.  **Generation**: Writes the full paper following Scopus/IEEE formatting standards.
8.  **Review**: A strict "Reviewer Agent" scores the paper. If the score is low, the cycle repeats.

---

## 🛠️ Installation & Setup

### Prerequisites
*   Python 3.8+
*   (Optional) CUDA-enabled GPU for offline mode

### 1. Clone the Repository
```bash
git clone https://github.com/Ayush0135/Multi-layer-research-agent.git
cd Multi-layer-research-agent
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory:
```bash
cp .env.example .env
```
Edit `.env` and add your API keys:
```ini
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
GOOGLE_API_KEY=your_google_custom_search_api_key
GOOGLE_CSE_ID=your_search_engine_id
```

### 4. (Optional) Setup Offline Models
If you plan to run without API keys or as a fallback:
```bash
python setup_offline.py
```

---

## 🖥️ Usage

Run the main script and provide a research topic:

```bash
python main.py "The Impact of Quantum Computing on Cryptography"
```

**Or simply run interactive mode:**
```bash
python main.py
```

The agent will print its progress through the stages. Upon success, the final paper will be saved as `paper_topic_name_paper.md`.

---

## 📂 Project Structure

```
.
├── main.py                # Entry point & orchestration logic
├── requirements.txt       # Python dependencies
├── .env                   # API Secrets (Ignored by Git)
├── utils/
│   ├── llm.py             # Interface for Cloud LLMs (Gemini/Groq)
│   ├── llm_offline.py     # Interface for Local LLMs
│   └── search.py          # Google Search utilities
├── stages/
│   ├── stage1_topic.py      # Decomposition
│   ├── stage2_discovery.py  # Search
│   ├── stage3_analysis.py   # Content extraction
│   ├── stage4_scoring.py    # Academic ranking
│   ├── stage5_filtering.py  # Knowledge base selection
│   ├── stage6_synthesis.py  # Logical structuring
│   ├── stage7_generation.py # Drafting
│   └── stage8_review.py     # Quality control
└── README.md
```

## ⚠️ Note on Offline Mode
Offline mode requires significant RAM/VRAM. By default, it attempts to use `HuggingFaceTB/SmolLM2-1.7B-Instruct` or similar lightweight models. Edit `utils/llm_offline.py` to change the target model.

## 🤝 Contribution
Contributions are welcome! Please fork the repo and submit a PR for any enhancements or bug fixes.

## 📄 License
This project is licensed under the MIT License.
