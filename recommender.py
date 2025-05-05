import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from difflib import get_close_matches  # <-- for fuzzy matching

class ContentRecommender:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path, encoding="latin1")
        self.tfidf_matrix = None
        self.indices = None

    def prepare_model(self):
        print("Preparing model... 🚀")
        self.df = self.df.dropna(subset=['title', 'description', 'genres'])

        columns = ['title', 'description', 'genres']
        for optional in ['cast', 'director']:
            if optional not in self.df.columns:
                self.df[optional] = ''
            columns.append(optional)

        for col in columns:
            self.df[col] = self.df[col].astype(str).fillna('')

        self.df['combined'] = self.df[columns].agg(' '.join, axis=1)

        tfidf = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = tfidf.fit_transform(self.df['combined'])

        self.df['title_lower'] = self.df['title'].str.lower()
        self.indices = pd.Series(self.df.index, index=self.df['title_lower']).drop_duplicates()
        print("✅ Model prepared.")

    def recommend(self, query, top_n=5):
        query = query.lower()

        if self.indices is None:
            print("❌ Model not prepared!")
            return []

        # 1️⃣ Try exact title match first
        if query in self.indices:
            idx = self.indices[query]
            return self._get_recommendations(idx, top_n)

        # 2️⃣ Try fuzzy matching (e.g., "Taxy Driver" instead of "Taxi Driver")
        matches = get_close_matches(query, self.indices.index, n=1, cutoff=0.6)
        if matches:
            print(f"✅ Fuzzy match found: {matches[0]}")
            idx = self.indices[matches[0]]
            return self._get_recommendations(idx, top_n)

        # 3️⃣ Try keyword search in cast (actor names)
        cast_matches = self.df[self.df['cast'].str.lower().str.contains(query)]
        if not cast_matches.empty:
            print(f"✅ Found by actor match: {query}")
            return cast_matches.sample(n=min(top_n, len(cast_matches)))[['title', 'description', 'genres', 'cast']].to_dict(orient='records')

        # 4️⃣ Try general keyword search in combined fields
        keyword_matches = self.df[self.df['combined'].str.lower().str.contains(query)]
        if not keyword_matches.empty:
            print(f"✅ Found by keyword match: {query}")
            return keyword_matches.sample(n=min(top_n, len(keyword_matches)))[['title', 'description', 'genres']].to_dict(orient='records')

        print(f"❌ No match found for: {query}")
        return []

    def _get_recommendations(self, idx, top_n):
        cosine_sim = linear_kernel(self.tfidf_matrix[idx], self.tfidf_matrix).flatten()
        sim_scores = list(enumerate(cosine_sim))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:top_n+1]  # skip itself
        movie_indices = [i[0] for i in sim_scores]
        recommendations = self.df.iloc[movie_indices][['title', 'description', 'genres']].to_dict(orient='records')
        return recommendations
