import os
import requests
from bs4 import BeautifulSoup
import io
import PyPDF2
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

def google_search(query, num_results=5):
    """
    Performs a Google Custom Search.
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_API_KEY,
        'cx': GOOGLE_CSE_ID,
        'q': query,
        'num': num_results
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('items', [])
    except Exception as e:
        print(f"Error performing Google Search: {e}")
        return []

def download_and_parse(url):
    """
    Downloads content from a URL and extracts text.
    Handles HTML and basic PDF parsing.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '').lower()
        
        if 'application/pdf' in content_type or url.endswith('.pdf'):
            try:
                with io.BytesIO(response.content) as open_pdf_file:
                    reader = PyPDF2.PdfReader(open_pdf_file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text
            except Exception as e:
                print(f"Error parsing PDF {url}: {e}")
                return ""
        else:
            # Assume HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            # Kill all script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
            # Break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text

    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return ""
