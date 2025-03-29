import streamlit as st
from neo4j import GraphDatabase
import pandas as pd
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Neo4j connection details
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

class Neo4jConnection:
    def __init__(self):
        self.driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    
    def close(self):
        self.driver.close()
    
    def query(self, query, params=None):
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]
    
    def add_movie(self, movie_data):
        query = """
        CREATE (m:Movie {
            show_id: $show_id,
            title: $title,
            release_year: $release_year,
            rating: $rating,
            duration: $duration
        })
        WITH m
        UNWIND $directors as director
        MERGE (d:Director {name: director})
        MERGE (d)-[:DIRECTED]->(m)
        WITH m
        UNWIND $cast as actor
        MERGE (a:Actor {name: actor})
        MERGE (a)-[:ACTED_IN]->(m)
        WITH m
        UNWIND $countries as country
        MERGE (c:Country {name: country})
        MERGE (m)-[:RELEASED_IN]->(c)
        WITH m
        UNWIND $genres as genre
        MERGE (g:Genre {name: genre})
        MERGE (m)-[:BELONGS_TO_GENRE]->(g)
        """
        with self.driver.session() as session:
            session.run(query, movie_data)

def main():
    st.title("📝 Add New Content")
    
    # Initialize Neo4j connection
    neo4j = Neo4jConnection()
    
    # Create form
    with st.form("add_movie_form"):
        # Basic Information
        st.header("Basic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Title")
            release_year = st.number_input("Release Year", min_value=1900, max_value=datetime.now().year)
            rating = st.selectbox("Rating", ["G", "PG", "PG-13", "R", "NC-17", "TV-Y", "TV-Y7", "TV-Y7-FV", "TV-G", "TV-PG", "TV-14", "TV-MA"])
        
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=1000)
            show_id = st.text_input("Show ID (unique identifier)")
        
        # Lists
        st.header("Additional Information")
        
        # Directors
        directors_input = st.text_area("Directors (comma-separated)")
        directors = [d.strip() for d in directors_input.split(",")] if directors_input else []
        
        # Cast
        cast_input = st.text_area("Cast (comma-separated)")
        cast = [c.strip() for c in cast_input.split(",")] if cast_input else []
        
        # Countries
        countries_input = st.text_area("Countries (comma-separated)")
        countries = [c.strip() for c in countries_input.split(",")] if countries_input else []
        
        # Genres
        genres_input = st.text_area("Genres (comma-separated)")
        genres = [g.strip() for g in genres_input.split(",")] if genres_input else []
        
        # Submit button
        submitted = st.form_submit_button("Add Movie")
        
        if submitted:
            try:
                movie_data = {
                    "show_id": show_id,
                    "title": title,
                    "release_year": release_year,
                    "rating": rating,
                    "duration": duration,
                    "directors": directors,
                    "cast": cast,
                    "countries": countries,
                    "genres": genres
                }
                
                neo4j.add_movie(movie_data)
                st.success("Movie added successfully!")
                
                # Clear form
                st.experimental_rerun()
                
            except Exception as e:
                st.error(f"Error adding movie: {str(e)}")
    
    # Preview existing data
    st.header("Preview Existing Data")
    
    # Show sample movies
    preview_query = """
    MATCH (m:Movie)
    RETURN m.title as title, m.release_year as year, m.rating as rating
    LIMIT 5
    """
    preview_data = neo4j.query(preview_query)
    preview_df = pd.DataFrame(preview_data)
    st.dataframe(preview_df)
    
    # Close Neo4j connection
    neo4j.close()

if __name__ == "__main__":
    main() 