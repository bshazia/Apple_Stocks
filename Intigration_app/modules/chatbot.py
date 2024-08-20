from datetime import datetime
import json
import locale
from flask import Flask, jsonify, request
from openai import OpenAI
import requests
import os
import re
import urllib.parse
import urllib.request
from dotenv import load_dotenv


load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = Flask(__name__)

def detect_language(query):
    if re.search(r'[\u0600-\u06FF]', query):
        return 'ar'
    else:
        return 'en'

def get_today_date(language):
    try:
        if language == 'ar':
            locale.setlocale(locale.LC_TIME, 'ar_SA.UTF-8')
        else:
            locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')

    today_date = datetime.now().strftime('%A, %B %d, %Y')
    return today_date


def google_search(query):
    
        api_key = os.getenv('GOOGLE_CSE_API_KEY')
        cse_id = os.getenv('GOOGLE_CSE_ID')
  
       
        #print(api_key,cse_id)
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.googleapis.com/customsearch/v1?q={encoded_query}&key={api_key}&cx={cse_id}&num=2"
        response = requests.get(url)
        data = response.json()

       # print(f"Response Data: {data}") 
        if 'items' in data:
            print(f"Response Data: {data['items']}") 
            return data['items']
        else:
            return None
    

def summarize_search_results(user_query, search_results, language):
    if not search_results:
        return "No relevant information found." if language == 'en' else "لم يتم العثور على معلومات ذات صلة."

    results_info = []
    for item in search_results:
        title = item.get('title', '')
        snippet = item.get('snippet', '')
        results_info.append(f"Title: {title}\nSnippet: {snippet}" if language == 'en' else f"العنوان: {title}\nمقتطف: {snippet}")

    context = "\n\n".join(results_info)
    prompt = (
        f"Given the User query: {user_query}\nLanguage: {language}\n"
        "extract relevant information from the provided text or information and generate a concise answer based on that data. Ensure the response is in the appropriate language based on the user's input language.\n\n"
        f"To the user's question:\n\n{context}"
    )
  
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an assistant that extracts precise information asked by the user in the user's question based on the provided information."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error during OpenAI request: {e}")
        return "Unable to generate response from OpenAI."

def chat_response(user_query, language):
    prompt = (
        f"User query: {user_query}\nLanguage: {language}\n"
        "Generate an appropriate response. If you don't have the information, "
        "trigger the google_search function to fetch more details or "
        "the get_today_date function if the query asks for today's date."
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a chatbot that provides relevant responses based on the user's query and detected language. If you don't have the information, trigger the google_search function to retrieve more details or the get_today_date function if the query asks for today's date."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            functions=[
                {
                    "name": "google_search",
                    "description": "Performs a Google search using a given query and returns the search results.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query to be used for retrieving information from Google."}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "get_today_date",
                    "description": "Returns today's date in the appropriate format based on the user's language.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "language": {"type": "string", "description": "The language in which to return the date."}
                        },
                        "required": ["language"]
                    }
                }
            ]
        )

        if completion.choices[0].finish_reason == "function_call":
            function_args = json.loads(completion.choices[0].message.function_call.arguments)

            if completion.choices[0].message.function_call.name == "google_search":
                search_results = google_search(function_args["query"])
                response = summarize_search_results(user_query, search_results, language)
            elif completion.choices[0].message.function_call.name == "get_today_date":
                response = get_today_date(function_args["language"])
            else:
                response = "Unknown function call."

        else:
            response = completion.choices[0].message.content
            print(response)

        return response
    except Exception as e:
        print(f"Error during OpenAI request: {e}")
        return "Unable to generate response from OpenAI."

@app.route('/chatbot', methods=['POST'])
def chat():
    user_query = request.json.get('query', '')
    language = detect_language(user_query)
    response = chat_response(user_query, language)
    return jsonify({'response': response})

def test_chatgpt_api():
    my_assistant = client.beta.assistants.create(
        instructions="You are a chatbot that provides relevant responses based on the user's query and detected language.",
        name="chat bot",
        tools=[{"type": "code_interpreter"}],
        model="gpt-4o",
    )
    print(my_assistant)

    return (print('hhh'))
    
@app.route('/test', methods=['GET'])
def test_api():
    #print("hhhhhhhhh")
    result = test_chatgpt_api()
    return jsonify({"result": result})
if __name__ == '__main__':
    app.run(debug=True)
    
