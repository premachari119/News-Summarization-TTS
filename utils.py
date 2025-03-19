import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from gtts import gTTS
import base64
import io
import logging
import time
import random
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
    revision="714eb0f"
)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

@retry(wait=wait_exponential(multiplier=1, max=10), stop=stop_after_attempt(3))
def fetch_url(url):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response

def extract_data_with_bs4(url, selectors):
    try:
        response = fetch_url(url)
        soup = BeautifulSoup(response.content, "html.parser")
        extracted_data = {}
        for label, selector in selectors.items():
            elements = soup.select(selector)
            if elements:
                extracted_data[label] = " ".join(element.get_text(strip=True) for element in elements)
            else:
                extracted_data[label] = None
        return extracted_data
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error fetching {url}: {e}")
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return None

def get_news_data(company_name, urls):
    articles = []
    for url in urls:
        try:
            if "nasdaq.com" in url:
                selectors = {"title": ".quote-news__title", "summary": ".quote-news__desc"}
            elif "investopedia.com" in url:
                selectors = {"title": ".search-results__title-link", "summary": ".search-results__description"}
            else:
                selectors = {"title": "h1", "summary": "p"}

            data = extract_data_with_bs4(url, selectors)
            if data and data['title']:
                title = data['title']
                summary = data['summary'] if data['summary'] else "Summary not found."
                topics_element = BeautifulSoup(fetch_url(url).content, "html.parser").find("meta", attrs={"name": "keywords"})
                topics = topics_element["content"].split(",") if topics_element and topics_element["content"] else []
                articles.append({
                    "Title": title,
                    "Summary": summary,
                    "url": url,
                    "Topics": topics,
                })
            time.sleep(random.uniform(3, 7))
        except Exception as e:
            logger.exception(f"Error processing {url}: {e}")
    return articles

def analyze_news_data(news_data):
    try:
        sentiments = []
        for article in news_data:
            sentiment_result = sentiment_pipeline(article["Title"])[0]
            sentiments.append(sentiment_result["label"])
            article["Sentiment"] = sentiment_result["label"]

        positive_count = sentiments.count("POSITIVE")
        negative_count = sentiments.count("NEGATIVE")
        neutral_count = sentiments.count("NEUTRAL")

        final_sentiment = "Positive" if positive_count > negative_count else "Negative" if negative_count > positive_count else "Neutral"

        coverage_differences = []
        for i in range(len(news_data)):
            for j in range(i + 1, len(news_data)):
                comparison = f"Article {i + 1} highlights {news_data[i]['Title']}, while Article {j + 1} discusses {news_data[j]['Title']}."
                impact = f"Article {i + 1} is {news_data[i]['Sentiment']}, while Article {j + 1} is {news_data[j]['Sentiment']}."
                coverage_differences.append({"Comparison": comparison, "Impact": impact})

        all_topics = [article.get('Topics', []) for article in news_data]
        all_topics_flat = [topic for sublist in all_topics for topic in sublist]
        common_topics = list(set([topic for topic in all_topics_flat if all_topics_flat.count(topic) > 1]))
        unique_topics = {}
        for i, article in enumerate(news_data):
            unique_topics[f"Unique Topics in Article {i + 1}"] = [topic for topic in article.get('Topics', []) if topic not in common_topics]

        comparative_scores = {
            "Sentiment Distribution": {"Positive": positive_count, "Negative": negative_count, "Neutral": neutral_count},
            "Coverage Differences": coverage_differences,
            "Topic Overlap": {"Common Topics": common_topics, **unique_topics},
        }

        result = {
            "Articles": news_data,
            "Comparative Sentiment Score": comparative_scores,
            "Final Sentiment Analysis": final_sentiment,
        }
        logger.info(f"Sentiment analysis result: {result}")
        return result
    except Exception as e:
        logger.exception(f"Error during sentiment analysis: {e}")
        return {
            "Articles": [],
            "Comparative Sentiment Score": {
                "Sentiment Distribution": {"Positive": 0, "Negative": 0, "Neutral": 0},
                "Coverage Differences": [],
                "Topic Overlap": {"Common Topics": []},
            },
            "Final Sentiment Analysis": "Neutral",
        }

def generate_tts_audio(text):
    try:
        logger.info(f"Generating TTS for text: {text}")
        tts = gTTS(text=text, lang="hi")
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_bytes = mp3_fp.getvalue()
        audio_base64 = base64.b64encode(mp3_bytes).decode("utf-8")
        logger.info("TTS audio generated successfully.")
        return audio_base64
    except Exception as e:
        logger.exception(f"Error during TTS: {e}")
        return ""