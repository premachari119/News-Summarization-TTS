import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from utils import get_news_data, analyze_news_data, generate_audio_summary
import logging
from googlesearch import search
import asyncio
import requests
from bs4 import BeautifulSoup

app = FastAPI()
logging.basicConfig(level=logging.DEBUG)

class CompanyRequest(BaseModel):
    company_name: str

async def fetch_articles(company_name: str, num_articles: int = 5) -> list:
    """Fetches news articles from Google and specific sources."""
    urls = []
    try:
        search_results = list(search(f"news about {company_name}", num_results=num_articles, lang="en"))
        urls.extend(search_results)
    except Exception as e:
        logging.error(f"Google search error: {e}")

    # Add specific news sources (example)
    specific_sources = [
        f"https://www.reuters.com/search/news?blob={company_name}",
        f"https://www.bloomberg.com/search?query={company_name}",
    ]
    for source in specific_sources:
        try:
            response = requests.get(source)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            # Extract article links from the specific source (adjust selectors)
            article_links = [a["href"] for a in soup.find_all("a", href=True) if company_name.lower() in a["href"].lower()]
            urls.extend(article_links[:3])#limit to 3 per site.
        except Exception as e:
            logging.error(f"Error fetching from {source}: {e}")

    # Filter out problematic URLs
    filtered_urls = [url for url in urls if "investors.com" not in url and "tesla.com" not in url]
    return filtered_urls[:10]#Limit to 10 total urls.

@app.post("/analyze")
async def analyze(request: CompanyRequest):
    company_name = request.company_name
    try:
        urls = await fetch_articles(company_name)
        if not urls:
            raise HTTPException(status_code=404, detail="No articles found.")
        news_data = get_news_data(company_name, urls)
        analysis = analyze_news_data(news_data, company_name)
        audio = generate_audio_summary(analysis["Final Sentiment Analysis"], company_name) #Corrected Line
        return {"Articles": analysis["Articles"], "Comparative Sentiment Score": analysis["Comparative Sentiment Score"], "Final Sentiment Analysis": analysis["Final Sentiment Analysis"], "Audio": audio}
    except Exception as e:
        logging.exception("Analysis error")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def index():
    return {"message": "News API"}