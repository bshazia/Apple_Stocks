from flask import Flask, request, jsonify
from config import Config
from modules.chatbot import chat_response, detect_language  
from modules.article_writer import extract
from modules.video_summary import summarize_video
from modules.video_shortener import short_video
from modules.text_classifier import classify

app = Flask(__name__)
app.config.from_object(Config)

@app.route('/')
def home():
    return "Welcome to the MY Flask Application!"


@app.route('/video/summary', methods=['POST'])
def video_summary():
    data = request.json
    video_url = data.get('video_url')
    language = data.get('language')
    type_of_summary = data.get('type_of_summary')
    
    if not video_url or not language or not type_of_summary:
        return jsonify({'error': 'Missing required parameters'}), 400

    response_data, status_code = summarize_video(video_url=video_url, language=language, type_of_summary=type_of_summary)
    
    return jsonify(response_data), status_code


@app.route('/video/shorten', methods=['POST'])
def video_shorten():
    return short_video()  


@app.route('/chatbot', methods=['POST'])
def chat():
    user_query = request.json.get('query', '')
    language = detect_language(user_query)
    response = chat_response(user_query, language)
    return jsonify({'response': response})


@app.route('/article', methods=['POST'])
def article_writer():
    topic = request.form.get('topic')
    file = request.files.get('file')  
    url = request.form.get('url') 

    response, status_code = extract(topic=topic, file=file, url=url)
    return jsonify(response), status_code

@app.route('/text/classify', methods=['POST'])
def text_classify():
    data = request.json
    text = data.get('text')

    if not text:
        title = data.get('Title')
        description = data.get('Description')

        if not title and not description:
            return jsonify({'error': 'At least one of title or description must be provided'}), 400

        text = (title or '') + ' ' + (description or '')

    response = classify(text=text)
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)
