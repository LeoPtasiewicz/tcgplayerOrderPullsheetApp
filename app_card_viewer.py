from flask import Flask, render_template, jsonify, request
import pandas as pd
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Load the CSV file
df = pd.read_csv('combined_order_details.csv')

print(df.head())  # Print the first few rows for debugging

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
DISCORD_WEBHOOK_CHATBOT_URL = os.getenv('DISCORD_WEBHOOK_CHATBOT_URL')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/card/<int:card_id>')
def get_card(card_id):
    if 0 <= card_id < len(df):
        card = df.iloc[card_id]
        card_data = {
            'ProductName': card['Product Name'],
            'ProductURL': card['Product URL'],
            'Condition': card['Condition'],
            'Quantity': int(card['Quantity']),  # Convert to regular integer
            'ImageURL': card['Image URL'],
            'SetCode': card['Set Code'] if pd.notna(card['Set Code']) else 'N/A',
            'ReleaseDate': card['Release Date'] if pd.notna(card['Release Date']) else 'N/A',
            'Name': card['Name'] if pd.notna(card['Name']) else 'N/A',
            'Code': card['Code'] if pd.notna(card['Code']) else 'N/A'
        }
        return jsonify(card_data)
    else:
        return jsonify({'error': 'Card not found'}), 404

@app.route('/products')
def get_products():
    products = df[['Product Name', 'Quantity']].to_dict(orient='records')
    return jsonify(products)

@app.route('/flag', methods=['POST'])
def flag_card():
    card_id = request.json.get('card_id')
    if 0 <= card_id < len(df):
        card = df.iloc[card_id]
        card_data = {
            'ProductName': card['Product Name'],
            'ProductURL': card['Product URL'],
            'Condition': card['Condition'],
            'Quantity': int(card['Quantity']),  # Convert to regular integer
            'ImageURL': card['Image URL'],
            'SetCode': card['Set Code'] if pd.notna(card['Set Code']) else 'N/A',
            'ReleaseDate': card['Release Date'] if pd.notna(card['Release Date']) else 'N/A',
            'Name': card['Name'] if pd.notna(card['Name']) else 'N/A',
            'Code': card['Code'] if pd.notna(card['Code']) else 'N/A'
        }
        message = (
            f"**Product Name:** {card_data['ProductName']}\n"
            f"**Product URL:** {card_data['ProductURL']}\n"
            f"**Condition:** {card_data['Condition']}\n"
            f"**Quantity:** {card_data['Quantity']}\n"
            f"**Set Code:** {card_data['SetCode']}\n"
            f"**Release Date:** {card_data['ReleaseDate']}\n"
            f"**Name:** {card_data['Name']}\n"
            f"**Code:** {card_data['Code']}\n"
            f"**Image URL:** {card_data['ImageURL']}"
        )
        payload = {
            'content': message
        }
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            return jsonify({'success': 'Card flagged successfully'}), 200
        else:
            return jsonify({'error': 'Failed to send message to Discord'}), 500
    else:
        return jsonify({'error': 'Card not found'}), 404

@app.route('/chatbot', methods=['POST'])
def chatbot():
    chat_log = request.json.get('chat_log')
    payload = {
        'content': chat_log
    }
    response = requests.post(DISCORD_WEBHOOK_CHATBOT_URL, json=payload)
    if response.status_code == 204:
        return jsonify({'success': 'Chat log sent successfully'}), 200
    else:
        return jsonify({'error': 'Failed to send chat log to Discord'}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("Copy paste this into a new bash terminal:\n$ /d/ngrok.exe start my_custom_domain")
    app.run(host='0.0.0.0', port=port, debug=True)
    