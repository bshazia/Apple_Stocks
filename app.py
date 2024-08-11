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

# PDF
def text_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Website 
def text_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    text = ' '.join(p.get_text() for p in soup.find_all('p'))
    return text


def is_topic_intext(text, topic):
    return topic.lower() in text.lower()

def detect_language(text):
    prompt = f"Detect the language of the following text: '{text}'. Please respond with only the language name."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an assistant that detects the language of a given text."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=20,
            temperature=0
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error detecting language: {str(e)}"

def translate(text, target_language):
    prompt = f"Translate the following text to {target_language}: '{text}'."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an assistant that translates text to a specified language."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0
        )
        translated_text = response.choices[0].message.content.strip()
        print(translated_text,"  hhhhhhhhh")
        if "translates to" in translated_text:
            translated_text = translated_text.split("translates to")[-1].strip().strip("'\"")

        if "in English." in translated_text:
            translated_text = translated_text.replace("in English.", "").strip().strip("'\"")

        translated_text = translated_text.strip("'\"").strip()
        
        return translated_text
    except Exception as e:
        return f"Error translating text: {str(e)}"

def split_text(text, max_length=4096):
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        if len(' '.join(current_chunk) + ' ' + word) > max_length:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
        else:
            current_chunk.append(word)
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def generate_article(text, topic, language):
    chunks = split_text(text)
    relevant_chunk = None
    
    for chunk in chunks:
        if is_topic_intext(chunk, topic):
            relevant_chunk = chunk
            break

    if not relevant_chunk:
        return "The provided topic is not mentioned in there."

    prompt = f"Write an article in {language} about '{topic}' based only on the following information: {relevant_chunk}"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an assistant that writes articles based on only the information provided here."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating article: {str(e)}"

@app.route('/extract', methods=['POST'])
def extract():
    try:
        topic = request.form.get('topic')
        original_topic_language = detect_language(topic)
        print(original_topic_language)
        if "error" in original_topic_language.lower():
            return jsonify({"error": original_topic_language}), 500

        if 'file' in request.files:
            file = request.files.get('file')

            if file and topic:
                try:
                    text = text_pdf(file)
                    text_language = detect_language(text)
                    print("text_language :", {text_language})
                    if original_topic_language != text_language:
                        print("in the if 1")
                        topic = translate(topic, text_language)
                        print("in the if 1 with topic ",{topic})
                    if not is_topic_intext(text, topic):
                        return jsonify({"error": "The provided topic is not mentioned in the document."}), 400

                    article = generate_article(text, topic, text_language)
                    
                    if original_topic_language != text_language:
                        article = translate(article, original_topic_language)
                    
                    
                    return jsonify({"article": article})
                except Exception as e:
                    return jsonify({"error": f"Error processing PDF file: {str(e)}"}), 500
            else:
                return jsonify({"error": "No PDF file or topic provided"}), 400

        elif 'url' in request.form:
            url = request.form.get('url')

            if url and topic:
                try:
                    text = text_website(url)
                    text_language = detect_language(text)
                    
                    if original_topic_language != text_language:
                        topic = translate(topic, text_language)
                    
                    if not is_topic_intext(text, topic):
                        return jsonify({"error": "The provided topic is not mentioned on the website."}), 400

                    article = generate_article(text, topic, text_language)
                    
                    if original_topic_language != text_language:
                        article = translate(article, original_topic_language)
                    
                    return jsonify({"article": article})
                except Exception as e:
                    return jsonify({"error": f"Error processing URL: {str(e)}"}), 500
            else:
                return jsonify({"error": "No URL or topic provided"}), 400

        return jsonify({"error": "No file or URL given"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
