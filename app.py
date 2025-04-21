import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# Load movie data from SQL
engine = create_engine("sqlite:///media_recommendations.db")

# Load movies and recommendations
movies_df = pd.read_sql("SELECT * FROM movies", engine)
recommendations_df = pd.read_sql("SELECT * FROM recommendations", engine)

# Streamlit UI
st.set_page_config(page_title="Hidden Gems Movie Finder", layout="wide")

st.title("🎬 Hidden Gems Movie Finder")
st.write("Discover underrated movies and get personalized recommendations!")

# 📌 Show Top 10 Hidden Gems
st.subheader("🔍 Top 10 Hidden Gems")
hidden_gems = movies_df.sort_values(by="underrated_score", ascending=False).head(10)

for _, row in hidden_gems.iterrows():
    st.markdown(f"**🎥 [{row['title']}]({row['url']})**  \n⭐ {row['rating']} | 👍 {row['votes']} votes | 🎭 {row['genre']}")

# 📌 Search for Movie Recommendations
st.subheader("🔎 Find Movie Recommendations")

selected_movie = st.selectbox("Choose a movie:", movies_df["title"].tolist())

if selected_movie:
    movie_id = movies_df[movies_df["title"] == selected_movie]["movie_id"].values[0]
    recs = recommendations_df[recommendations_df["movie_id"] == movie_id].head(10)

    if not recs.empty:
        st.subheader(f"🎞️ Movies similar to {selected_movie}:")
        for _, rec in recs.iterrows():
            movie_info = movies_df[movies_df["movie_id"] == rec["recommended_movie_id"]]
            if not movie_info.empty:
                row = movie_info.iloc[0]
                st.markdown(f"**🎥 [{row['title']}]({row['url']})**  \n⭐ {row['rating']} | 👍 {row['votes']} votes | 🎭 {row['genre']}")

# 📌 Footer
st.write("---")
st.write("🎭 **Built with love using Streamlit** | 📊 **Data from IMDb**")
