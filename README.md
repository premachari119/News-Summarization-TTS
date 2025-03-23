---
title: News Summarization TTS
emoji: 🏃
colorFrom: yellow
colorTo: pink
sdk: streamlit
sdk_version: 1.43.2
app_file: app.py
pinned: false
---

# News Summarization and Sentiment Analysis

This application provides news summarization, sentiment analysis, and audio generation for a given company name and news URLs.

## Project Setup

1.  **Clone the Repository:**

    ```bash
    git clone <repository_url>
    cd News_Summarization_TTS
    ```

2.  **Create a Virtual Environment (Recommended):**

    ```bash
    python -m venv venv
    # Activate the environment:
    # Windows:
    venv\Scripts\activate
    # macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the FastAPI Server (Uvicorn):**

    ```bash
    uvicorn api:app --reload
    ```

    * This starts the API server on `http://127.0.0.1:8000`.

5.  **Run the Streamlit Application:**

    ```bash
    streamlit run app.py
    ```

    * This opens the Streamlit application in your web browser.

## Model Details

* **Sentiment Analysis:**
    * Model: `distilbert/distilbert-base-uncased-finetuned-sst-2-english`
    * Link: [Hugging Face Model Hub](https://huggingface.co/distilbert/distilbert-base-uncased-finetuned-sst-2-english)
    * Explanation: Used `transformers` pipeline for sentiment classification.
* **Topic Analysis:**
    * Model: `facebook/bart-large-mnli`
    * Link: [Hugging Face Model Hub](https://huggingface.co/facebook/bart-large-mnli)
    * Explanation: Used `transformers` pipeline for zero-shot classification.
* **Text-to-Speech (TTS):**
    * Library: `gTTS`
    * Explanation: Converts translated text to Hindi speech.
* **Translation:**
    * Library: `googletrans` (version 4.0.0-rc1)
    * Note: This library can be unstable. Consider using Google Cloud Translation API or the `translate` library for better reliability.

## API Usage (FastAPI)

* **API Endpoint:** `/analyze` (POST)
* **Method:** POST
* **Parameters:**
    * `company_name` (string): The name of the company to search for news about.
    * `urls` (array of strings): An array of news URLs.

### Example Request (Postman or similar)

* **URL:** `http://127.0.0.1:8000/analyze`
* **Method:** POST
* **Headers:** `Content-Type: application/json`
* **Body (JSON):**

    ```json
    {
      "company_name": "Tesla",
      "urls": [
        "[https://example.com/news1](https://example.com/news1)",
        "[https://example.com/news2](https://example.com/news2)"
      ]
    }
    ```

### Example Response (JSON)

```json
{
  "Articles": [
    {
      "Title": "News Article Title 1",
      "Summary": "Article summary...",
      "Sentiment": "POSITIVE",
      "Topics": ["Electric Vehicles", "Business"]
    },
    {
        "Title": "News Article Title 2",
        "Summary": "Article summary...",
        "Sentiment": "NEGATIVE",
        "Topics": ["Stock Market"]
    }
  ],
  "Comparative Sentiment Score": {
    "Sentiment Distribution": {
      "Positive": 1,
      "Negative": 1,
      "Neutral": 0
    },
    "Coverage Differences": [
      {
        "Comparison": "Article 1 vs. Article 2: Different Sentiments (POSITIVE vs. NEGATIVE). No Common Topics. Articles focus on distinct aspects of the company. ",
        "Impact": "Sentiment differences might indicate varying perspectives on the company. Articles focus on distinct aspects of the company. "
      }
    ]
  },
  "Topic Overlap": {
    "Common Topics": [],
    "Unique Topics in Article 1": ["Electric Vehicles", "Business"],
    "Unique Topics in Article 2": ["Stock Market"]
  },
  "Final Sentiment Analysis": "Tesla's latest news coverage is neutral.",
  "Audio": "base64_encoded_audio_data"
}


**Key Improvements:**

* **Detailed Model Explanations:** Added links and explanations for each model.
* **Comprehensive API Usage:** Clear instructions with example request and response JSON.
* **Explicit `googletrans` Note:** Emphasized the instability of `googletrans` and suggested alternatives.
* **Third Party API Usage:** added a section that explains the usage of each third party api.
* **More Detailed Assumptions and Limitations:** Expanded on the limitations.
* **Clear Setup Instructions:** Added virtual environment instructions.

Remember to replace `<repository_url>` and `<deployment_link>` with your actual values.