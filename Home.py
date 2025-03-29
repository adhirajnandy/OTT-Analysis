import streamlit as st
from neo4j import GraphDatabase
import pandas as pd
import os
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
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

def main():
    st.set_page_config(
        page_title="Netflix Analysis Dashboard",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 Netflix Content Analysis Dashboard")
    
    # Initialize Neo4j connection
    neo4j = Neo4jConnection()
    
    # Quick Stats
    st.header("Quick Statistics")
    
    # Get total movies and TV shows
    content_query = """
    MATCH (m)
    WHERE m:Movie OR m:TVShow
    RETURN 
        CASE WHEN m:Movie THEN 'Movie' ELSE 'TV Show' END as type,
        count(*) as count
    """
    content_df = pd.DataFrame(neo4j.query(content_query))
    
    # Display metrics
    col1, col2 = st.columns(2)
    with col1:
        movies_count = content_df[content_df['type'] == 'Movie']['count'].iloc[0] if not content_df.empty else 0
        st.metric("Total Movies", movies_count)
    with col2:
        tvshows_count = content_df[content_df['type'] == 'TV Show']['count'].iloc[0] if not content_df.empty else 0
        st.metric("Total TV Shows", tvshows_count)
    
    # Node Type Distribution
    st.header("Content Type Distribution")
    fig = px.pie(content_df, values='count', names='type', 
                 title='Distribution of Movies vs TV Shows')
    st.plotly_chart(fig)
    
    # Get total actors and directors
    people_query = """
    MATCH (a:Actor)
    WITH count(a) as actor_count
    MATCH (d:Director)
    WITH actor_count, count(d) as director_count
    RETURN actor_count, director_count
    """
    people_df = pd.DataFrame(neo4j.query(people_query))
    
    # Display metrics for people
    col1, col2 = st.columns(2)
    with col1:
        actors_count = people_df['actor_count'].iloc[0] if not people_df.empty else 0
        st.metric("Total Actors", actors_count)
    with col2:
        directors_count = people_df['director_count'].iloc[0] if not people_df.empty else 0
        st.metric("Total Directors", directors_count)
    
    # Popular Genre Combinations
    st.header("Popular Genre Combinations")
    genre_query = """
    MATCH (m:Movie)-[:BELONGS_TO_GENRE]->(g:Genre)
    WITH m, collect(g.name) as genres
    RETURN genres, count(*) as count
    ORDER BY count DESC
    LIMIT 10
    """
    genre_df = pd.DataFrame(neo4j.query(genre_query))
    
    if not genre_df.empty:
        # Convert list of genres to string for visualization
        genre_df['genres'] = genre_df['genres'].apply(lambda x: ' + '.join(x))
        fig = px.pie(genre_df, values='count', names='genres', 
                    title='Top 10 Genre Combinations')
        st.plotly_chart(fig)
    
    # Custom Query Section
    st.sidebar.header("Custom Query")
    custom_query = st.sidebar.text_area("Enter your Cypher query:")
    if st.sidebar.button("Run Query"):
        if custom_query:
            try:
                results = neo4j.query(custom_query)
                if results:
                    st.sidebar.dataframe(pd.DataFrame(results))
                else:
                    st.sidebar.info("No results found.")
            except Exception as e:
                st.sidebar.error(f"Error executing query: {str(e)}")
        else:
            st.sidebar.warning("Please enter a query.")
    
    # Close Neo4j connection
    neo4j.close()

if __name__ == "__main__":
    main() 