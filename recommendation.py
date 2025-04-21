import pandas as pd
from sqlalchemy import create_engine

# Load movie data from SQL
engine = create_engine("sqlite:///media_recommendations.db")
movies_df = pd.read_sql("SELECT movie_id, title, genre FROM movies", engine)

# Preprocessing: Convert genres to sets for easy comparison
movies_df["genre_set"] = movies_df["genre"].apply(lambda x: set(x.split(", ")) if isinstance(x, str) else set())

def get_genre_similarity(movie_genres, other_genres):
    """Calculate genre similarity based on Jaccard similarity."""
    if not movie_genres or not other_genres:
        return 0
    return len(movie_genres & other_genres) / len(movie_genres | other_genres)

# Generate recommendations for each movie
recommendations = []

for i, row in movies_df.iterrows():
    movie_id = row["movie_id"]
    movie_genres = row["genre_set"]

    # Compute similarity with all other movies
    movies_df["similarity"] = movies_df["genre_set"].apply(lambda g: get_genre_similarity(movie_genres, g))

    # Get top 10 recommendations (excluding the movie itself)
    top_recommendations = movies_df[movies_df["movie_id"] != movie_id].nlargest(10, "similarity")

    for _, rec in top_recommendations.iterrows():
        recommendations.append([movie_id, rec["movie_id"], rec["similarity"]])

# Store recommendations in SQL
recommendations_df = pd.DataFrame(recommendations, columns=["movie_id", "recommended_movie_id", "similarity_score"])
recommendations_df.to_sql("recommendations", engine, if_exists="replace", index=False)

print("✅ Genre-based recommendations generated & stored in SQL!")
