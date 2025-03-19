import streamlit as st
import requests
import base64

API_URL = "http://127.0.0.1:5000/analyze"

def main():
    st.title("News Summarization and Sentiment Analysis")

    company_names = ["Tesla", "Apple", "Microsoft"]
    company_name = st.selectbox("Select Company:", company_names)

    if st.button("Analyze"):
        with st.spinner("Analyzing..."):
            if company_name:
                try:
                    response = requests.post(API_URL, json={"company": company_name})
                    response.raise_for_status()
                    result = response.json()

                    st.subheader(f"Sentiment Analysis for {company_name}")
                    st.json(result)

                    if "Audio" in result and result["Audio"]:
                        st.subheader("Audio Summary (Hindi)")
                        audio_base64 = result["Audio"]
                        audio_bytes = base64.b64decode(audio_base64)
                        st.audio(audio_bytes, format="audio/mp3")

                except requests.exceptions.HTTPError as e:
                    st.error(f"API Error: {e.response.status_code} - {e.response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error connecting to API: {e}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
            else:
                st.warning("Please select a company name.")

if __name__ == "__main__":
    main()