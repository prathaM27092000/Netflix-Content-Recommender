from flask_cors import CORS
from flask import Flask, request, jsonify, render_template
from recommender import ContentRecommender
import os

app = Flask(__name__)
CORS(app)  # <-- this line corrected!

# ✅ Use absolute path to content.csv
csv_path = os.path.join(os.path.dirname(__file__), 'content.csv')
recommender = ContentRecommender(csv_path)
recommender.prepare_model()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.get_json()
        title = data.get('title', '')
        if not title:
            return jsonify({'error': 'No title provided'}), 400

        recommendations = recommender.recommend(title)
        return jsonify({'recommendations': recommendations}), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
