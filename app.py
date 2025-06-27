import pickle
import streamlit as st
import requests
import pandas as pd
import os

# ---- ✅ Safe Google Drive Downloader for Large Files ----
def download_from_google_drive(file_id, destination):
    def get_confirm_token(response):
        for key, value in response.cookies.items():
            if key.startswith("download_warning"):
                return value
        return None

    def save_response_content(response, destination):
        CHUNK_SIZE = 32768
        with open(destination, "wb") as f:
            for chunk in response.iter_content(CHUNK_SIZE):
                if chunk:
                    f.write(chunk)

    URL = "https://drive.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params={"id": file_id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {"id": file_id, "confirm": token}
        response = session.get(URL, params=params, stream=True)

    save_response_content(response, destination)

# ---- ✅ Download similarity.pkl if not present ----
if not os.path.exists('similarity.pkl'):
    with st.spinner("Downloading similarity data from Google Drive..."):
        file_id = "1xrCK3zV4Iy6aC3W3Bm8oLtX5kowNJFmo"
        download_from_google_drive(file_id, "similarity.pkl")
        st.success("Download complete!")

# ---- ✅ Load data safely ----
try:
    with open('similarity.pkl', 'rb') as f:
        similarity = pickle.load(f)
except Exception as e:
    st.error("❌ Failed to load similarity.pkl — it may be corrupted or incomplete.")
    st.stop()

with open('movie_list_dict.pkl', 'rb') as f:
    loaded_dict = pickle.load(f)
movies = pd.DataFrame(loaded_dict)

# ---- ✅ Fetch movie poster ----
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        return f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else "https://via.placeholder.com/150?text=No+Poster"
    except requests.exceptions.RequestException as e:
        print(f"Error fetching poster: {e}")
        return "https://via.placeholder.com/150?text=Error"

# ---- ✅ Recommend movies ----
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []
    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movie_names.append(movies.iloc[i[0]].title)
        recommended_movie_posters.append(fetch_poster(movie_id))
    return recommended_movie_names, recommended_movie_posters

# ---- ✅ Streamlit UI ----
st.set_page_config(page_title="Movie Recommender", layout="wide")
st.title('🎬 Movie Recommender System')

movie_list = movies['title'].values
selected_movie = st.selectbox("Type or select a movie from the dropdown", movie_list)

if st.button('Show Recommendation'):
    with st.spinner("Fetching recommendations..."):
        names, posters = recommend(selected_movie)
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            st.text(names[i])
            st.image(posters[i])
