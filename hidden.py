import pandas as pd
from sqlalchemy import create_engine
import numpy as np

# Load movie data from SQL
engine = create_engine("sqlite:///media_recommendations.db")
movies_df = pd.read_sql("SELECT * FROM movies", engine)

# Compute Underrated Score
movies_df["underrated_score"] = (movies_df["sentiment_score"] * movies_df["rating"]) / (np.log1p(movies_df["votes"]) + 1)

# Sort movies by underrated score (higher = more underrated)
movies_df = movies_df.sort_values(by="underrated_score", ascending=False)

# Save back to SQL
movies_df.to_sql("movies", engine, if_exists="replace", index=False)

print("✅ Hidden gems detected & updated in SQL!")