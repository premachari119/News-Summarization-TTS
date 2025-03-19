from flask import Flask, request, jsonify
from utils import get_news_data, analyze_news_data, generate_tts_audio
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

company_articles = {
    "Tesla": [
        "https://www.nasdaq.com/market-activity/stocks/tsla/news",
        "https://www.investopedia.com/search?q=tesla",
    ],
    "Apple": [
        "https://www.nasdaq.com/market-activity/stocks/aapl/news",
        "https://www.investopedia.com/search?q=apple",
    ],
    "Microsoft": [
        "https://www.nasdaq.com/market-activity/stocks/msft/news",
        "https://www.investopedia.com/search?q=microsoft",
    ],
}

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        company_name = data.get("company")

        if not company_name:
            return jsonify({"error": "Company name is required"}), 400

        urls = company_articles.get(company_name)
        if not urls:
            return jsonify({"error": "Company not found"}), 404

        news_data = get_news_data(company_name, urls)
        analysis_result = analyze_news_data(news_data)

        hindi_text = analysis_result["Final Sentiment Analysis"]
        audio_base64 = generate_tts_audio(hindi_text)

        output = {
            "Company": company_name,
            **analysis_result,
            "Audio": audio_base64,
        }

        return jsonify(output)

    except Exception as e:
        logger.exception(f"Error processing request: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route("/", methods=["GET"])
def index():
    return "News Summarization and Sentiment Analysis"

if __name__ == "__main__":
    app.run(debug=True)
    
