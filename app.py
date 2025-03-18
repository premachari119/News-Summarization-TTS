import streamlit as st
import requests
import base64

st.title("News Sentiment Analysis")
company = st.text_input("Enter Company Name")

if st.button("Analyze"):
    try:
        response = requests.post("http://127.0.0.1:8000/analyze", json={"company_name": company}) #Replace with your api url
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        result = response.json()
        st.write(result)

        audio_base64 = result.get("Audio")
        if audio_base64:
            audio_bytes = base64.b64decode(audio_base64)
            st.audio(audio_bytes, format="audio/mpeg")
        else:
            st.warning("No audio available.")

    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")