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
    
    # Genre distribution query
    genre_query = """
    MATCH (n:Movie)-[:BELONGS_TO_GENRE]->(g:Genre)
    RETURN g.name as genre, count(n) as count
    ORDER BY count DESC
    LIMIT 10
    """
    genre_data = neo4j.query(genre_query)
    genre_df = pd.DataFrame(genre_data)
    
    # Create treemap visualization
    fig = px.treemap(genre_df, path=['genre'], values='count',
                     title='Genre Distribution (Treemap)')
    st.plotly_chart(fig, use_container_width=True)
    
    # Genre combinations
    st.subheader("Popular Genre Combinations")
    combo_query = """
    MATCH (m:Movie)-[:BELONGS_TO_GENRE]->(g:Genre)
    WITH m, collect(g.name) as genres
    RETURN genres, count(*) as count
    ORDER BY count DESC
    LIMIT 10
    """
    combo_data = neo4j.query(combo_query)
    combo_df = pd.DataFrame(combo_data)
    
    # Create sunburst chart
    fig = px.sunburst(combo_df, path=['genres'], values='count',
                      title='Genre Combinations (Sunburst)')
    st.plotly_chart(fig, use_container_width=True)
    
    # Genre by Country
    st.header("Genre Distribution by Country")
    country_genre_query = """
    MATCH (m:Movie)-[:BELONGS_TO_GENRE]->(g:Genre),
          (m)-[:RELEASED_IN]->(c:Country)
    RETURN c.name as country, g.name as genre, count(*) as count
    ORDER BY count DESC
    LIMIT 20
    """
    country_genre_data = neo4j.query(country_genre_query)
    country_genre_df = pd.DataFrame(country_genre_data)
    
    # Create heatmap
    pivot_df = country_genre_df.pivot(index='country', columns='genre', values='count').fillna(0)
    fig = px.imshow(pivot_df, title='Genre Distribution by Country (Heatmap)')
    st.plotly_chart(fig, use_container_width=True)
    
    # Genre trends over time
    st.header("Genre Trends Over Time")
    trend_query = """
    MATCH (m:Movie)-[:BELONGS_TO_GENRE]->(g:Genre)
    WHERE m.release_year IS NOT NULL
    RETURN m.release_year as year, g.name as genre, count(*) as count
    ORDER BY year, genre
    """
    trend_data = neo4j.query(trend_query)
    trend_df = pd.DataFrame(trend_data)
    
    # Create line chart
    fig = px.line(trend_df, x='year', y='count', color='genre',
                  title='Genre Trends Over Time')
    st.plotly_chart(fig, use_container_width=True)
    
    # Close Neo4j connection
    neo4j.close()

if __name__ == "__main__":
    main() 