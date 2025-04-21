import torch
from transformers import pipeline
import pandas as pd
from sqlalchemy import create_engine

# Load IMDb review data from SQL
engine = create_engine("sqlite:///media_recommendations.db")

reviews_df = pd.read_sql("SELECT * FROM reviews", engine)

# Load Hugging Face sentiment analysis model
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

def analyze_sentiment(text):
    """Returns sentiment score: 1 for positive, 0 for negative."""
    result = sentiment_pipeline(text[:512])[0]  # Limit text to 512 tokens
    return 1 if result["label"] == "POSITIVE" else 0

# Perform sentiment analysis on reviews
reviews_df["sentiment"] = reviews_df["review_text"].apply(analyze_sentiment)

# Compute sentiment score for each movie (average of all reviews)
movie_sentiment = reviews_df.groupby("movie_id")["sentiment"].mean().reset_index()
movie_sentiment.rename(columns={"sentiment": "sentiment_score"}, inplace=True)

# Update sentiment scores in the movies table
movies_df = pd.read_sql("SELECT * FROM movies", engine)
movies_df = movies_df.merge(movie_sentiment, on="movie_id", how="left")

# Store updated movie data back into SQL
movies_df.to_sql("movies", engine, if_exists="replace", index=False)

print("✅ Sentiment analysis completed & updated in SQL!")
