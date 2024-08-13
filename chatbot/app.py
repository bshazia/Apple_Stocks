from flask import Flask, jsonify, request
import openai
import requests
import os
import re
from datetime import datetime
from urllib.parse import urlencode


openai.api_key = os.getenv('API_KEY')

app = Flask(__name__)

def detect_language(query):
    if re.search(r'[\u0600-\u06FF]', query):
        return 'ar'
    else:
        return 'en'



def google_search(query):
    try:
        api_key = os.getenv('GOOGLE_CSE_API_KEY')
        cse_id = os.getenv('GOOGLE_CSE_ID')

        
        encoded_query = requests.utils.quote(query)

        url = f"https://www.googleapis.com/customsearch/v1?q={encoded_query}&key={api_key}&cx={cse_id}&num=5"  
        print(f"Requesting URL: {url}") 
        response = requests.get(url)
        response.raise_for_status() 
        
        data = response.json()
        print(f"Response Data: {data}") 

        return data.get('items', [])
    except requests.RequestException as e:
        print(f"Error during Google search: {e}")
        return []

  

def summarize_search_results(search_results):
    if not search_results:
        return "No relevant information found."

    snippets = [item.get('snippet', '') for item in search_results]
    context = " ".join(snippets)

    prompt = f"Based on the following information, answer the question concisely in one sentence: {context}"

    try:
        response = openai.Completion.create(
            engine="gpt-4-omini",  
            prompt=prompt,
            max_tokens=50
        )
        return response.choices[0].text.strip()
    except openai.OpenAIError as e:
        print(f"Error during OpenAI request: {e}")
        return "Unable to generate response from OpenAI."

def get_current_date(language):
    now = datetime.now()
    if language == 'ar':
        return f"التاريخ الحالي هو {now.strftime('%Y-%m-%d')}"
    else:
        return f"The current date is {now.strftime('%Y-%m-%d')}"

@app.route('/chatbot', methods=['POST'])
def chat():
    """Handle the chat request and provide appropriate responses."""
    user_query = request.json.get('query', '')
    language = detect_language(user_query)

    if 'hi' in user_query.lower() or 'hello' in user_query.lower():
        response = "Hello! How can I assist you today?" if language == 'en' else "مرحبا! كيف يمكنني مساعدتك اليوم؟"
    elif 'date' in user_query.lower():
        response = get_current_date(language)
    else:
        search_results = google_search(user_query)
        response = summarize_search_results(search_results)

    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)
