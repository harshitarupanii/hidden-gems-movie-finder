import requests
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine
import numpy as np
import re
import time

# IMDb Top 250 URL
URL = "https://www.imdb.com/chart/top/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def convert_votes(vote_str):
    """Converts IMDb votes from '3M' or '915K' to an integer."""
    try:
        vote_str = str(vote_str).strip().replace(',', '')
        if not vote_str:
            return 0
            
        if 'M' in vote_str or 'm' in vote_str:
            return int(float(vote_str.lower().replace('m', '')) * 1_000_000)
        elif 'K' in vote_str or 'k' in vote_str:
            return int(float(vote_str.lower().replace('k', '')) * 1_000)
        elif '.' in vote_str:  # Handle cases like '1.2M' which we might have missed
            return int(float(vote_str) * 1_000_000 if 'M' in vote_str.upper() else int(float(vote_str) * 1_000))
        else:
            return int(vote_str)
    except Exception as e:
        print(f"Error converting votes: {vote_str} - {e}")
        return 0

def get_movie_genre(movie_url):
    """Fetches the genre of a movie from its IMDb page."""
    try:
        response = requests.get(movie_url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")
        genre_tag = soup.select("span.ipc-chip__text")
        genres = ", ".join([g.text.strip() for g in genre_tag]) if genre_tag else "Unknown"
        return genres
    except Exception as e:
        print(f"❌ Error fetching genre for {movie_url}: {e}")
        return "Unknown"

def scrape_imdb_movies(url):
    """Scrapes movie details from IMDb Top 250 page."""
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    movies = []
    rows = soup.select("li.ipc-metadata-list-summary-item")

    for row in rows:
        try:
            # Title extraction
            title_tag = row.select_one("h3.ipc-title__text")
            title = title_tag.text.split('. ', 1)[1] if title_tag else "Unknown"

            movie_url_tag = row.select_one("a.ipc-lockup-overlay")
            movie_url = "https://www.imdb.com" + movie_url_tag["href"] if movie_url_tag else "N/A"
            movie_id = re.search(r"/title/(tt\d+)/", movie_url)
            movie_id = movie_id.group(1) if movie_id else None

            # Improved rating and votes extraction
            rating_tag = row.select_one("span.ipc-rating-star--imdb")
            if rating_tag:
                # Extract rating
                rating_text = rating_tag.text.strip()
                rating = float(rating_text.split()[0])
                
                # New method to extract votes
                votes_tag = row.select_one("span.ipc-rating-star--voteCount")
                if votes_tag:
                    votes_text = votes_tag.text.strip()
                    # Remove parentheses and any non-numeric characters
                    votes_text = votes_text.replace('(', '').replace(')', '').replace(',', '')
                    votes = convert_votes(votes_text)
                else:
                    votes = 0
            else:
                rating, votes = np.nan, 0

            genre = get_movie_genre(movie_url)
            genre = genre.replace("Back to top", "").strip(" ,")
            
            movies.append([movie_id, title, genre, rating, votes, movie_url])

        except Exception as e:
            print(f"❌ Error scraping a movie: {e}")

    df = pd.DataFrame(movies, columns=["movie_id", "title", "genre", "rating", "votes", "url"])
    df["underrated_score"] = df["rating"] / np.log1p(df["votes"])
    return df

def scrape_imdb_reviews(movie_id):
    """Scrapes IMDb reviews for a given movie ID."""
    review_url = f"https://www.imdb.com/title/{movie_id}/reviews"
    response = requests.get(review_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    reviews = []
    review_blocks = soup.select("div.review-container")[:10]  # First 10 reviews

    for block in review_blocks:
        try:
            review_text_tag = block.select_one("div.text.show-more__control")
            review_text = review_text_tag.text.strip() if review_text_tag else None

            if review_text:
                reviews.append([movie_id, review_text])

        except Exception as e:
            print(f"❌ Error scraping a review: {e}")

    return reviews

# Initialize SQL database
engine = create_engine("sqlite:///media_recommendations.db")

# Scrape IMDb movies
movies_df = scrape_imdb_movies(URL)
movies_df.to_sql("movies", engine, if_exists="replace", index=False)

# Scrape IMDb reviews
all_reviews = []
for movie_id in movies_df["movie_id"]:
    if movie_id:
        print(f"🔍 Scraping reviews for {movie_id}...")
        reviews = scrape_imdb_reviews(movie_id)
        all_reviews.extend(reviews)
        time.sleep(1)  # Avoid IMDb blocking

reviews_df = pd.DataFrame(all_reviews, columns=["movie_id", "review_text"])
reviews_df.to_sql("reviews", engine, if_exists="replace", index=False)

print("✅ IMDb movie & review data scraped & stored in SQL!")