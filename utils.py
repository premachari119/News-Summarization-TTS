import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from gtts import gTTS, gTTSError
import base64
import io
import logging
import random
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from googletrans import Translator
import time

# Initialize logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("gtts.tts").setLevel(logging.WARNING)  # Suppress gTTS warnings
logging.getLogger("urllib3").setLevel(logging.WARNING)  # Suppress urllib3 warnings

# Initialize sentiment analysis pipeline
try:
    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
        revision="714eb0f"
    )
except Exception as e:
    logger.critical(f"Failed to load sentiment analysis model: {e}")

# Initialize topic analysis pipeline
try:
    topic_pipeline = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
except Exception as e:
    logger.critical(f"Failed to load topic analysis model: {e}")

# User agent list for more robust scraping
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

# Retry decorator for handling network errors
@retry(wait=wait_exponential(multiplier=1, max=10), stop=stop_after_attempt(3),
       retry=(retry_if_exception_type(requests.exceptions.ConnectionError) | retry_if_exception_type(requests.exceptions.HTTPError)))
def fetch_url(url):
    """Fetches the content of a URL with retry logic and error handling."""
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"URL not found: {url}")
            return None
        else:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        raise
    time.sleep(2)
    return None

def extract_data_with_bs4(url, selectors):
    """Extracts data from a URL using BeautifulSoup, handling potential errors."""
    try:
        response = fetch_url(url)
        if response is None:
            return None
        soup = BeautifulSoup(response.content, "html.parser")
        extracted_data = {}
        for label, selector in selectors.items():
            elements = soup.select(selector)
            if elements and elements[0].get_text(strip=True) and elements[0].get_text(
                    strip=True) != "Read More" and elements[0].get_text(strip=True) != "My Account" and elements[
                0].get_text(strip=True) != "Credit Cards":
                extracted_data[label] = elements[0].get_text(strip=True)
            else:
                extracted_data[label] = None
        return extracted_data
    except Exception as e:
        logger.error(f"Error extracting data from {url}: {e}")
        return None

def generate_tts_audio(text, lang="hi"):
    """Generates TTS audio from text using gTTS, with error handling."""
    try:
        tts = gTTS(text=text, lang=lang)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        audio_base64 = base64.b64encode(mp3_fp.getvalue()).decode("utf-8")
        return audio_base64
    except Exception as e:
        logger.error(f"Error generating TTS audio: {e}")
        return ""

def get_news_data(company_name, urls):
    """Retrieves news data from a list of URLs."""
    news_data = []
    for url in urls:
        selectors = {
            "title": "h1",
            "summary": "p"
        }
        extracted_data = extract_data_with_bs4(url, selectors)
        if extracted_data:
            if not extracted_data["title"]:
                extracted_data["title"] = "No Title Found"
            if not extracted_data["summary"]:
                extracted_data["summary"] = "No Summary Found"
            news_data.append({
                "Title": extracted_data['title'],
                "Summary": extracted_data['summary']
            })
        else:
            news_data.append({
                "Title": "404 Error",
                "Summary": "Failed to retrieve article content."
            })
    return news_data

def analyze_news_data(news_data, company_name):
    articles = []
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    all_topics = []

    for article in news_data:
        if not article['Summary'] or article['Summary'] == "No Summary Found" or article[
            'Title'] == "404 Error" or article['Title'] == "JavaScript is not available.":
            sentiment = "Neutral"
            topics = []
        else:
            try:
                sentiment_result = sentiment_pipeline(article['Summary'])
                sentiment = sentiment_result[0]['label']
            except Exception as e:
                logger.error(f"Error in sentiment analysis: {e}")
                sentiment = "Neutral"
            try:
                candidate_labels = ["Stock Market", "Electric Vehicles", "Autonomous Vehicles", "Regulations",
                                    "Innovation", "Finance", "Technology", "Business"]
                topic_result = topic_pipeline(article['Summary'], candidate_labels)
                topics = [topic_result['labels'][i] for i in range(len(topic_result['labels'])) if
                          topic_result['scores'][i] > 0.5]
            except Exception as e:
                logger.error(f"Error in topic analysis: {e}")
                topics = []

        articles.append({
            "Title": article['Title'],
            "Summary": article['Summary'],
            "Sentiment": sentiment,
            "Topics": topics
        })
        all_topics.extend(topics)

        if sentiment == "POSITIVE":
            positive_count += 1
        elif sentiment == "NEGATIVE":
            negative_count += 1
        else:
            neutral_count += 1

    comparative_analysis = {
        "Sentiment Distribution": {
            "Positive": positive_count,
            "Negative": negative_count,
            "Neutral": neutral_count
        },
        "Coverage Differences": [],
    }

    if len(articles) > 1:
        comparative_analysis["Coverage Differences"] = []
        for i in range(len(articles)):
            for j in range(i + 1, len(articles)):
                if not articles[i]['Summary'] or not articles[j]['Summary'] or \
                        articles[i]['Title'] == "404 Error" or articles[j]['Title'] == "404 Error" or \
                        articles[i]['Title'] == "JavaScript is not available." or \
                        articles[j]['Title'] == "JavaScript is not available.":
                    continue  # Skip comparison if either article is invalid

                comparison = f"Article {i + 1} vs. Article {j + 1}: "
                impact = ""

                # Sentiment Comparison
                if articles[i]['Sentiment'] != articles[j]['Sentiment']:
                    comparison += f"Different Sentiments ({articles[i]['Sentiment']} vs. {articles[j]['Sentiment']}). "
                    impact += "Sentiment differences might indicate varying perspectives on the company. "

                # Topic Overlap Comparison
                common_topics = set(articles[i]['Topics']) & set(articles[j]['Topics'])
                if common_topics:
                    comparison += f"Common Topics: {', '.join(common_topics)}. "
                    impact += "Shared topics suggest areas of agreement or focus. "
                else:
                    comparison += "No Common Topics. "
                    impact += "Articles focus on distinct aspects of the company. "

                # Keyword Comparison (Simple Approach)
                keywords_i = set(articles[i]['Summary'].lower().split()) if articles[i]['Summary'] else set()
                keywords_j = set(articles[j]['Summary'].lower().split()) if articles[j]['Summary'] else set()
                common_keywords = keywords_i & keywords_j
                if common_keywords:
                    comparison += f"Common Keywords: {', '.join(list(common_keywords)[:5])}. "  # Limit to 5 keywords
                    impact += "Shared keywords suggest related content. "
                else:
                    comparison += "No Common Keywords. "
                    impact += "Articles have distinct content. "

                if comparison.endswith(": "):
                    continue  # Skip if no comparison was made

                comparative_analysis["Coverage Differences"].append({
                    "Comparison": comparison.strip(),
                    "Impact": impact.strip()
                })

    # Calculate Topic Overlap here, only if there are at least 2 articles with topics
    valid_topic_articles = [article for article in articles if article['Topics']]

    if len(valid_topic_articles) >= 2:
        common_topics = list(set([topic for topic in all_topics if all_topics.count(topic) > 1]))
        if len(valid_topic_articles) > 1 and valid_topic_articles[0]['Topics'] and valid_topic_articles[1]['Topics']: #Additional check
            unique_topics_article1 = list(set(valid_topic_articles[0]['Topics']) - set(valid_topic_articles[1]['Topics']))
            unique_topics_article2 = list(set(valid_topic_articles[1]['Topics']) - set(valid_topic_articles[0]['Topics']))
        else:
            unique_topics_article1 = []
            unique_topics_article2 = []
    elif valid_topic_articles:  # Handle cases where there is only one article with topics.
        common_topics = valid_topic_articles[0]['Topics']
        unique_topics_article1 = valid_topic_articles[0]['Topics']
        unique_topics_article2 = []
    elif len(articles) == 1: # Combine the cases into a single if/elif/else block
        common_topics = articles[0]['Topics'] if articles[0]['Topics'] else [] #handle cases where article has no topics
        unique_topics_article1 = articles[0]['Topics'] if articles[0]['Topics'] else []
        unique_topics_article2 = []
    else:
        common_topics = []
        unique_topics_article1 = []
        unique_topics_article2 = []

    # Make the final sentiment dynamic
    if positive_count > negative_count:
        final_sentiment = f"{company_name}'s latest news coverage is mostly positive. Potential stock growth expected for {company_name}."
    elif negative_count > positive_count:
        final_sentiment = f"{company_name}'s latest news coverage is mostly negative. Potential stock decline expected for {company_name}."
    else:
        final_sentiment = f"{company_name}'s latest news coverage is neutral."

    return {
        "Articles": articles,
        "Comparative Sentiment Score": comparative_analysis,
        "Topic Overlap": {
            "Common Topics": common_topics,
            "Unique Topics in Article 1": unique_topics_article1,
            "Unique Topics in Article 2": unique_topics_article2
        },
        "Final Sentiment Analysis": final_sentiment,
        "Audio": generate_audio_summary(final_sentiment, company_name)
    }
    
    
def generate_audio_summary(final_sentiment, company_name):
    translator = Translator()
    try:
        print(f"Final Sentiment (English): {final_sentiment}") #debugging
        translated_summary = translator.translate(final_sentiment, src='en', dest='hi').text
        print(f"Translated Summary (Hindi): {translated_summary}") #debugging
        logging.info(f"Translated summary: {translated_summary}")
        tts = gTTS(text=translated_summary, lang="hi")
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        audio_base64 = base64.b64encode(mp3_fp.getvalue()).decode("utf-8")
        print(f"API Base64 Length: {len(audio_base64)}")
        print(f"API Base64: {audio_base64}")
        return audio_base64
    except Exception as e:
        logging.error(f'Audio generation failed: {e}')
        print(f"Audio Generation Error: {e}")
        return ""



def generate_tts_audio(text, lang="hi"):
    """Generates TTS audio from text using gTTS, with error handling."""
    try:
        tts = gTTS(text=text, lang=lang)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        audio_base64 = base64.b64encode(mp3_fp.getvalue()).decode("utf-8")
        return audio_base64
    except Exception as e:
        logging.error(f"Error generating TTS audio: {e}")
        return ""