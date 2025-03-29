import streamlit as st
from neo4j import GraphDatabase
import pandas as pd
import os
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go

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
    st.title("🎬 Genre Analysis")
    
    # Initialize Neo4j connection
    neo4j = Neo4jConnection()
    
    # Genre Distribution
    st.header("Genre Distribution")
    genre_query = """
    MATCH (g:Genre)
    WITH g.name as genre, count(*) as count
    ORDER BY count DESC
    LIMIT 10
    RETURN genre, count
    """
    genre_df = pd.DataFrame(neo4j.query(genre_query))
    fig = px.pie(genre_df, values='count', names='genre', title='Top 10 Genres')
    st.plotly_chart(fig)
    
    # Genre Combinations
    st.header("Genre Combinations")
    combo_query = """
    MATCH (m:Movie)-[:BELONGS_TO_GENRE]->(g:Genre)
    WITH m, collect(g.name) as genres
    WITH genres, count(*) as count
    ORDER BY count DESC
    LIMIT 10
    RETURN genres, count
    """
    combo_df = pd.DataFrame(neo4j.query(combo_query))
    
    # Convert list to string for visualization
    combo_df['genres'] = combo_df['genres'].apply(lambda x: ' + '.join(x))
    
    fig = px.bar(combo_df, x='genres', y='count',
                 title='Top Genre Combinations')
    st.plotly_chart(fig)
    
    # Genre Trends Over Time
    st.header("Genre Trends Over Time")
    trend_query = """
    MATCH (m:Movie)-[:BELONGS_TO_GENRE]->(g:Genre)
    WHERE m.release_year IS NOT NULL
    WITH m.release_year as year, g.name as genre, count(*) as count
    ORDER BY year, genre
    RETURN year, genre, count
    """
    trend_df = pd.DataFrame(neo4j.query(trend_query))
    
    fig = px.line(trend_df, x='year', y='count', color='genre',
                  title='Genre Trends Over Time')
    st.plotly_chart(fig)
    
    # Genre Distribution by Country
    st.header("Genre Distribution by Country")
    country_query = """
    MATCH (m:Movie)-[:BELONGS_TO_GENRE]->(g:Genre)
    MATCH (m)-[:RELEASED_IN]->(c:Country)
    WITH c.name as country, g.name as genre, count(*) as count
    ORDER BY count DESC
    LIMIT 20
    RETURN country, genre, count
    """
    country_df = pd.DataFrame(neo4j.query(country_query))
    
    fig = px.bar(country_df, x='country', y='count', color='genre',
                 title='Genre Distribution by Country')
    st.plotly_chart(fig)
    
    # Close Neo4j connection
    neo4j.close()

if __name__ == "__main__":
    main() 