from flask import Flask, jsonify, request
import requests
import os
import re
from datetime import datetime

app = Flask(__name__)

def detect_language(query):
    if re.search(r'[\u0600-\u06FF]', query):
        return 'ar'
    else:
        return 'en'

def google_search(query):
    api_key = os.getenv('GOOGLE_CSE_API_KEY')
    cse_id = os.getenv('GOOGLE_CSE_ID')

    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cse_id}"
    response = requests.get(url)
    data = response.json()

    if 'items' in data:
        return data['items']
    else:
        return None

def extract_weather_info(snippet):
    match = re.search(r'(\d+°C|\d+°F)', snippet, re.IGNORECASE)
    if match:
        return f"Current temperature is {match.group(0)}."
    return None

def extract_stock_info(snippet):
    # print(snippet)
    if 'stock' in snippet.lower() or 'price' in snippet.lower():
        return snippet
    return None

def extract_news_info(snippet):
    if 'news' in snippet.lower():
        return snippet
    return None

def extract_currency_info(snippet):
    if 'currency' in snippet.lower() or 'exchange' in snippet.lower():
        return snippet
    return None

def extract_crypto_info(snippet):
    if 'crypto' in snippet.lower() or 'bitcoin' in snippet.lower() or 'ethereum' in snippet.lower():
        return snippet
    return None

def extract_sports_info(snippet):
    if 'score' in snippet.lower() or 'sports' in snippet.lower():
        return snippet
    return None

def extract_flight_info(snippet):
    if 'flight' in snippet.lower() or 'status' in snippet.lower():
        return snippet
    return None

def extract_public_transport_info(snippet):
    if 'transport' in snippet.lower() or 'bus' in snippet.lower() or 'train' in snippet.lower():
        return snippet
    return None

def extract_market_trends_info(snippet):
    if 'market' in snippet.lower() or 'trends' in snippet.lower():
        return snippet
    return None

def extract_info_from_search(query, search_results):
    best_snippet = None
    best_match_score = 0

    for item in search_results:
        snippet = item.get('snippet', '')
        
        if 'weather' in query.lower():
            if re.search(r'weather|temperature|forecast', snippet, re.IGNORECASE):
                weather_info = extract_weather_info(snippet)
                if weather_info:
                    return weather_info
        elif 'stock' in query.lower() or 'price' in query.lower():
            stock_info = extract_stock_info(snippet)
            print(stock_info)
            if stock_info:
                return stock_info
        elif 'news' in query.lower():
            news_info = extract_news_info(snippet)
            if news_info:
                return news_info
        elif 'currency' in query.lower() or 'exchange' in query.lower():
            currency_info = extract_currency_info(snippet)
            if currency_info:
                return currency_info
        elif 'crypto' in query.lower():
            crypto_info = extract_crypto_info(snippet)
            if crypto_info:
                return crypto_info
        elif 'sports' in query.lower() or 'score' in query.lower():
            sports_info = extract_sports_info(snippet)
            if sports_info:
                return sports_info
        elif 'flight' in query.lower() or 'status' in query.lower():
            flight_info = extract_flight_info(snippet)
            if flight_info:
                return flight_info
        elif 'transport' in query.lower() or 'bus' in query.lower() or 'train' in query.lower():
            public_transport_info = extract_public_transport_info(snippet)
            if public_transport_info:
                return public_transport_info
        elif 'market' in query.lower() or 'trends' in query.lower():
            market_trends_info = extract_market_trends_info(snippet)
            if market_trends_info:
                return market_trends_info

        match_score = 0
        if 'weather' in snippet.lower():
            match_score += 1
        if 'stock' in snippet.lower() or 'price' in snippet.lower():     
            match_score += 1
           # print(match_score)
        if 'news' in snippet.lower():
            match_score += 1
        if 'currency' in snippet.lower() or 'exchange' in snippet.lower():
            match_score += 1
        if 'crypto' in snippet.lower():
            match_score += 1
        if 'sports' in snippet.lower() or 'score' in snippet.lower():
            match_score += 1
        if 'flight' in snippet.lower() or 'status' in snippet.lower():
            match_score += 1
        if 'transport' in snippet.lower() or 'bus' in snippet.lower() or 'train' in snippet.lower():
            match_score += 1
        if 'market' in snippet.lower() or 'trends' in snippet.lower():
            match_score += 1

        if match_score > best_match_score:
            best_match_score = match_score
            best_snippet = snippet

    return best_snippet if best_snippet else "No relevant information found."

def get_current_date(language):
    now = datetime.now()
    if language == 'ar':
        return f"التاريخ الحالي هو {now.strftime('%Y-%m-%d')}"
    else:
        return f"The current date is {now.strftime('%Y-%m-%d')}"

def extract_city_from_query(query):
    match = re.search(r'weather in (\w+)', query, re.IGNORECASE)
    return match.group(1) if match else None

def get_weather(city, language):
    if language == 'ar':
        return f"هذه هي حالة الطقس الحالية في {city}."
    else:
        return f"This is the current weather in {city}."

def extract_stock_symbol(query):
    match = re.search(r'stock\s+(\w+)', query, re.IGNORECASE)
    return match.group(1) if match else None

def get_stock_price(stock_symbol, language):
    if stock_symbol:
        if language == 'ar':
            return f"هذه هي سعر السهم لـ {stock_symbol}."
        else:
            return f"This is the stock price for {stock_symbol}."
    else:
        return "Stock symbol not specified in the query."

@app.route('/chatbot', methods=['POST'])
def chat():
    user_query = request.json.get('query', '')
    language = detect_language(user_query)

    if 'date' in user_query.lower():
        response = get_current_date(language)
    elif 'weather' in user_query.lower():
        city = extract_city_from_query(user_query)
        if city:
            search_results = google_search(f'current weather in {city}')
            if search_results:
                response = extract_info_from_search(user_query, search_results)
            else:
                response = get_weather(city, language) + " Data not available."
        else:
            response = "City not specified in the query."
    elif 'stock' in user_query.lower():
        stock_symbol = extract_stock_symbol(user_query)
        if stock_symbol:
            search_results = google_search(f'stock news for {stock_symbol}')
            if search_results:
                response = extract_info_from_search(user_query, search_results)
            else:
                response = get_stock_price(stock_symbol, language) + " Data not available."
        else:
            response = "Stock symbol not specified in the query."
    elif 'news' in user_query.lower():
        search_results = google_search(f'latest news')
        if search_results:
            response = extract_info_from_search(user_query, search_results)
        else:
            response = "No news information available."
    elif 'currency' in user_query.lower() or 'exchange' in user_query.lower():
        search_results = google_search(f'currency exchange rates')
        if search_results:
            response = extract_info_from_search(user_query, search_results)
        else:
            response = "No currency information available."
    elif 'crypto' in user_query.lower():
        search_results = google_search(f'latest cryptocurrency prices')
        if search_results:
            response = extract_info_from_search(user_query, search_results)
        else:
            response = "No cryptocurrency information available."
    elif 'sports' in user_query.lower() or 'score' in user_query.lower():
        search_results = google_search(f'latest sports scores')
        if search_results:
            response = extract_info_from_search(user_query, search_results)
        else:
            response = "No sports information available."
    elif 'flight' in user_query.lower() or 'status' in user_query.lower():
        search_results = google_search(f'flight status')
        if search_results:
            response = extract_info_from_search(user_query, search_results)
        else:
            response = "No flight information available."
    elif 'transport' in user_query.lower() or 'bus' in user_query.lower() or 'train' in user_query.lower():
        search_results = google_search(f'public transport timetables')
        if search_results:
            response = extract_info_from_search(user_query, search_results)
        else:
            response = "No public transport information available."
    elif 'market' in user_query.lower() or 'trends' in user_query.lower():
        search_results = google_search(f'market trends')
        if search_results:
            response = extract_info_from_search(user_query, search_results)
        else:
            response = "No market trends information available."
    else:
        search_results = google_search(user_query)
        if search_results:
            response = extract_info_from_search(user_query, search_results)
        else:
            response = "No results found."

    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)
    