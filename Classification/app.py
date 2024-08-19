from flask import Flask, request, jsonify
import joblib

app = Flask(__name__)

model = joblib.load('news_classifier_model.pkl')

@app.route('/classify', methods=['POST'])
def classify():
    data = request.json
    title = data.get('Title')
    description = data.get('Description')
    
    if not title and not description:
        return jsonify({'error': 'At least one of title or description must be provided'}), 400
    

    text = (title or '') + ' ' + (description or '')
    
    prediction = model.predict([text])
    category = prediction[0]
    
    return jsonify({'category': category})

if __name__ == '__main__':
    app.run(debug=True)
