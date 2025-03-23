import streamlit as st
import requests
import json
import base64

def main():
    st.title("News Summarization and Sentiment Analysis")

    company_name = st.text_input("Enter Company Name:")
    if st.button("Get News Report"):
        if company_name:
            try:
                api_url = "http://127.0.0.1:8000/analyze"
                payload = {"company_name": company_name}
                headers = {"Content-Type": "application/json"}
                response = requests.post(api_url, data=json.dumps(payload), headers=headers)
                response.raise_for_status()
                result = response.json()

                if "Articles" in result:
                    st.subheader("Articles:")
                    for article in result["Articles"]:
                        st.markdown(f"**Title:** {article['Title']}")
                        st.write(f"**Summary:** {article['Summary']}")
                        st.write(f"**Sentiment:** {article['Sentiment']}")
                        st.write(f"**Topics:** {', '.join(article['Topics'])}")
                        st.write("---")

                if "Comparative Sentiment Score" in result:
                    st.subheader("Comparative Sentiment Score:")
                    st.write(f"**Sentiment Distribution:** {result['Comparative Sentiment Score']['Sentiment Distribution']}")
                    st.write("**Coverage Differences:**")
                    for comparison in result['Comparative Sentiment Score']['Coverage Differences']:
                        st.write(f"- {comparison['Comparison']}  Impact: {comparison['Impact']}")

                if "Topic Overlap" in result:
                    st.subheader("Topic Overlap:")
                    st.write(f"**Common Topics:** {result['Topic Overlap']['Common Topics']}")
                    st.write(f"**Unique Topics in Article 1:** {result['Topic Overlap']['Unique Topics in Article 1']}")
                    st.write(f"**Unique Topics in Article 2:** {result['Topic Overlap']['Unique Topics in Article 2']}")

                if "Final Sentiment Analysis" in result:
                    st.subheader("Final Sentiment Analysis:")
                    st.write(result["Final Sentiment Analysis"])

                if "Audio" in result and result["Audio"]:
                    st.subheader("Audio Summary (Hindi)")
                    audio_base64 = result["Audio"]
                    try: 
                        audio_bytes = base64.b64decode(audio_base64)
                        st.audio(audio_bytes, format="audio/mp3")
                    except Exception as e:
                        st.error(f"Error playing audio: {e}")

            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching data: {e}")
            except json.JSONDecodeError as e:
                st.error(f"Error decoding JSON response: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
        else:
            st.warning("Please enter a company name.")

if __name__ == "__main__":
    main()