import pandas as pd
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')

def load_data():
    try:
        m_df = pd.read_csv('movies_100k.csv', sep='|', encoding='latin-1', header=None, on_bad_lines='skip')
        m_df = m_df[[0, 1]].rename(columns={0: 'movieId', 1: 'title'})
        m_df['movieId'] = pd.to_numeric(m_df['movieId'], errors='coerce')
        m_df = m_df.dropna(subset=['movieId'])
        
        r_df = pd.read_csv('ratings_100k.csv', sep=None, engine='python', encoding='latin-1', header=None, on_bad_lines='skip')
        r_df = r_df[[0, 1, 2]].rename(columns={0: 'userId', 1: 'movieId', 2: 'rating'})
        for col in r_df.columns:
            r_df[col] = pd.to_numeric(r_df[col], errors='coerce')
        r_df = r_df.dropna()
        return m_df, r_df
    except Exception:
        return None, None

movies, ratings = load_data()

def get_popular():
    if ratings is None: return []
    stats = ratings.groupby('movieId')['rating'].agg(['mean', 'count'])
    top_ids = stats[stats['count'] > 50].sort_values('mean', ascending=False).head(20).index
    return movies[movies['movieId'].isin(top_ids)]['title'].tolist()

popular_list = get_popular()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_movies')
def get_movies():
    if movies is None: return jsonify([])
    mlist = [{'movieId': int(row['movieId']), 'title': str(row['title'])} for _, row in movies.head(1000).iterrows()]
    return jsonify(mlist)

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    selected_ids = [int(i) for i in data.get('movieIds', []) if i and str(i).isdigit()]
    if not selected_ids:
        return jsonify({"recommendations": popular_list[:5]})
    try:
        users = ratings[(ratings['movieId'].isin(selected_ids)) & (ratings['rating'] >= 4)]['userId'].unique()
        sim = ratings[ratings['userId'].isin(users) & (~ratings['movieId'].isin(selected_ids))]
        if sim.empty: return jsonify({"recommendations": popular_list[:5]})
        res_ids = sim.groupby('movieId')['rating'].mean().sort_values(ascending=False).head(10).index
        res_titles = movies[movies['movieId'].isin(res_ids)]['title'].tolist()
        final = []
        for t in res_titles:
            if t not in final: final.append(t)
        if len(final) < 5:
            for p in popular_list:
                if p not in final: final.append(p)
        return jsonify({"recommendations": final[:5]})
    except:
        return jsonify({"recommendations": popular_list[:5]})

if __name__ == '__main__':
    app.run(debug=True, port=5000)