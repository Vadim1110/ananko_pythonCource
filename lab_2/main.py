import requests
import copy
import csv
from collections import namedtuple
from datetime import timedelta, datetime as d
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="API.env")
api_token = os.getenv("API_TOKEN")
api_root = "https://api.themoviedb.org/3"

class MovieDataTool:

    def __init__(self, num_pages):
        self.base_url = f"{api_root}/discover/movie"
        self.genre_url = f"{api_root}/genre/movie/list?language=en"
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {api_token}"
        }
        self.num_pages = num_pages
        self.movies = []
        self.genres = {}

    def fetch(self):
        self._fetch_movies()
        self._fetch_genres()

    def _fetch_movies(self):
        for page in range(1, self.num_pages + 1):
            params = {
                "include_adult": "false",
                "include_video": "false",
                "sort_by": "popularity.desc",
                "page": page,
            }
            response = requests.get(self.base_url, headers=self.headers, params=params)
            if response.status_code == 200:
                self.movies.extend(response.json().get("results", []))

    def _fetch_genres(self):
        response = requests.get(self.genre_url, headers=self.headers)
        if response.status_code == 200:
            self.genres = {genre["id"]: genre["name"] for genre in response.json().get("genres", [])}

    def get_all_data(self):
        return self.movies

    def get_selected_movies(self):
        return self.movies[3:20:4]

    def get_most_popular_title(self):
        return max(self.movies, key=lambda x: x.get("popularity", 0), default={}).get("title", "None")

    def get_titles_with_keywords(self, *keywords):
        return [movie['title'] for movie in self.movies
        if any(keyword.lower() in movie.get("overview", "").lower() for keyword in keywords)]

    def get_unique_genres(self):
        return frozenset(self.genres.values())

    def delete_movies_by_genre(self, genre_name):
        genre_id = list((gid for gid, name in self.genres.items() if name.lower() == genre_name.lower()))
        if genre_id:
            self.movies = [movie for movie in self.movies if genre_id[0] not in movie.get("genre_ids", [])]

    def get_most_popular_genres(self):
        genre_count = {}

        for movie in self.movies:
            for genre_id in movie.get("genre_ids", []):
                genre_name = self.genres.get(genre_id, "Unknown")
                genre_count[genre_name] = genre_count.get(genre_name, 0) + 1
        return sorted(genre_count.items(), key=lambda x: x[1], reverse=True)

    def get_movies_grouped_by_genre(self):
        genre_pairs = frozenset(
            (movie1["title"], movie2["title"]) for movie1 in self.movies for movie2 in self.movies
            if movie1 != movie2 and set(movie1.get("genre_ids", [])) & set(movie2.get("genre_ids", []))
        )
        return genre_pairs

    def get_initial_data_and_modified_copy(self):
        modified_copy = copy.deepcopy(self.movies)
        for movie in modified_copy:
            if "genre_ids" in movie and isinstance(movie["genre_ids"], list) and movie["genre_ids"]:
                movie["genre_ids"][0] = 22
        return self.movies, modified_copy

    def get_sorted_movie_data(self):
        MovieInfo = namedtuple("MovieInfo", ["title", "popularity", "score", "last_day_in_cinema"])
        sorted_movies = sorted(
            (
                MovieInfo(
                    title=movie["title"],
                    popularity=round(movie["popularity"], 1),
                    score=int(movie["vote_average"]),
                    last_day_in_cinema=d.strptime(movie["release_date"], "%Y-%m-%d") + timedelta(weeks=10)
                )
                for movie in self.movies if "release_date" in movie
            ),
            key=lambda x: (-x.score, -x.popularity)
        )
        return sorted_movies

    def save_sorted_movie_data_to_csv(self, file_path):
        sorted_movies = self.get_sorted_movie_data()
        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Title", "Popularity", "Score", "Last Day in Cinema"])
            writer.writerows(sorted_movies)
