import os
from flask import Flask, jsonify, request
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
from openai import OpenAI
from flask_cors import CORS

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = Flask(__name__)
CORS(app)


#print(os.getenv('OPENAI_API_KEY'))

#pdf 
def text_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

#website
def text_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    text = ' '.join(p.get_text() for p in soup.find_all('p'))
    return text
def is_topic_intext(text, topic):
    return topic.lower() in text.lower()


def generate_article(text, topic):
    prompt = f"Write an article about '{topic}' based on the following information:{text}"

    completion = client.chat.completions.create(
        model="gpt-4", 
        messages=[
            {"role": "system", "content": "You are an assistant that writes articles based on provided information."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    
    return completion.choices[0].message['content'].strip()

def test_chatgpt_api():
    print("chatgpt")
    try:
       
        response = client.chat.completions.create(
            model="gpt-4", 
            messages=[
                {"role": "user", "content": "Write a lesson plan for an introductory algebra class. The lesson plan should cover the distributive law, in particular how it works in simple cases involving mixes of positive and negative numbers. Come up with some examples that show common student errors."}
            ],
            temperature=0.7,
            max_tokens=64,
            top_p=1
        )
        print(response)
        return response.choices[0].message['content']
    except Exception as e:
        return f"Error testing ChatGPT API: {str(e)}"


@app.route('/extract', methods=['POST'])
def extract():
    topic = request.form.get('topic')
    
    if 'file' in request.files:
        
        file = request.files.get('file')

        if file and topic:
            try:
                text = text_pdf(file)
                if not is_topic_intext(text, topic):
                    return jsonify({"error": "The provided topic is not mentioned in the document."}), 400
               
                article = generate_article(text, topic)
                return jsonify({"article": article})
            except Exception as e:
                return jsonify({"error": f"Error processing PDF file: {str(e)}"}), 500
        return jsonify({"error": "No PDF file or topic provided"}), 400

    elif 'url' in request.form:
        url = request.form.get('url')

        if url and topic:
            try:
                text = text_website(url)
                if not is_topic_intext(text, topic):
                    return jsonify({"error": "The provided topic is not mentioned in the website."}), 400
                article = generate_article(text, topic)
                return jsonify({"article": article})
            except Exception as e:
                return jsonify({"error": f"Error processing URL: {str(e)}"}), 500
        return jsonify({"error": "No URL or topic provided"}), 400

    return jsonify({"error": "No file or URL given"}), 400

@app.route('/test', methods=['GET'])
def test_api():
    #print("hhhhhhhhh")
    result = test_chatgpt_api()
    return jsonify({"result": result})

if __name__ == '__main__':
    app.run(debug=True)