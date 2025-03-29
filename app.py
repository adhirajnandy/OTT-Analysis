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
    st.set_page_config(page_title="Netflix Graph Analysis", layout="wide")
    st.title("Netflix Content Analysis Dashboard")
    
    # Initialize Neo4j connection
    neo4j = Neo4jConnection()
    
    # Sidebar for different analysis options
    analysis_type = st.sidebar.selectbox(
        "Select Analysis Type",
        ["Overview", "Content Analysis", "Actor/Director Analysis", "Genre Analysis", "Country Analysis"]
    )
    
    if analysis_type == "Overview":
        st.header("Database Overview")
        
        # Get counts of different node types
        counts_query = """
        MATCH (n)
        RETURN labels(n)[0] as type, count(n) as count
        ORDER BY count DESC
        """
        counts = neo4j.query(counts_query)
        counts_df = pd.DataFrame(counts)
        
        # Create bar chart
        fig = px.bar(counts_df, x='type', y='count', title='Node Types Distribution')
        st.plotly_chart(fig, use_container_width=True)
        
        # Display relationship counts
        rel_counts_query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        ORDER BY count DESC
        """
        rel_counts = neo4j.query(rel_counts_query)
        rel_counts_df = pd.DataFrame(rel_counts)
        
        fig = px.bar(rel_counts_df, x='type', y='count', title='Relationship Types Distribution')
        st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "Content Analysis":
        st.header("Content Analysis")
        
        # Year distribution
        year_query = """
        MATCH (n:Movie)
        RETURN n.release_year as year, count(n) as count
        WHERE n.release_year IS NOT NULL
        ORDER BY year
        """
        year_data = neo4j.query(year_query)
        year_df = pd.DataFrame(year_data)
        
        fig = px.line(year_df, x='year', y='count', title='Movies Released by Year')
        st.plotly_chart(fig, use_container_width=True)
        
        # Rating distribution
        rating_query = """
        MATCH (n:Movie)
        RETURN n.rating as rating, count(n) as count
        WHERE n.rating IS NOT NULL
        ORDER BY count DESC
        """
        rating_data = neo4j.query(rating_query)
        rating_df = pd.DataFrame(rating_data)
        
        fig = px.pie(rating_df, values='count', names='rating', title='Rating Distribution')
        st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "Actor/Director Analysis":
        st.header("Actor/Director Analysis")
        
        # Top actors
        actor_query = """
        MATCH (a:Actor)-[:ACTED_IN]->(n)
        RETURN a.name as name, count(n) as movie_count
        ORDER BY movie_count DESC
        LIMIT 10
        """
        actor_data = neo4j.query(actor_query)
        actor_df = pd.DataFrame(actor_data)
        
        fig = px.bar(actor_df, x='name', y='movie_count', title='Top 10 Actors by Number of Movies')
        st.plotly_chart(fig, use_container_width=True)
        
        # Top directors
        director_query = """
        MATCH (d:Director)-[:DIRECTED]->(n)
        RETURN d.name as name, count(n) as movie_count
        ORDER BY movie_count DESC
        LIMIT 10
        """
        director_data = neo4j.query(director_query)
        director_df = pd.DataFrame(director_data)
        
        fig = px.bar(director_df, x='name', y='movie_count', title='Top 10 Directors by Number of Movies')
        st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "Genre Analysis":
        st.header("Genre Analysis")
        
        # Genre distribution
        genre_query = """
        MATCH (n:Movie)-[:BELONGS_TO_GENRE]->(g:Genre)
        RETURN g.name as genre, count(n) as count
        ORDER BY count DESC
        LIMIT 10
        """
        genre_data = neo4j.query(genre_query)
        genre_df = pd.DataFrame(genre_data)
        
        fig = px.bar(genre_df, x='genre', y='count', title='Top 10 Genres')
        st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "Country Analysis":
        st.header("Country Analysis")
        
        # Country distribution
        country_query = """
        MATCH (n:Movie)-[:RELEASED_IN]->(c:Country)
        RETURN c.name as country, count(n) as count
        ORDER BY count DESC
        LIMIT 10
        """
        country_data = neo4j.query(country_query)
        country_df = pd.DataFrame(country_data)
        
        fig = px.bar(country_df, x='country', y='count', title='Top 10 Countries by Number of Movies')
        st.plotly_chart(fig, use_container_width=True)
    
    # Custom query section
    st.sidebar.header("Custom Query")
    custom_query = st.sidebar.text_area("Enter your Cypher query")
    if st.sidebar.button("Run Query"):
        try:
            results = neo4j.query(custom_query)
            st.sidebar.dataframe(pd.DataFrame(results))
        except Exception as e:
            st.sidebar.error(f"Error executing query: {str(e)}")
    
    # Close Neo4j connection
    neo4j.close()

if __name__ == "__main__":
    main() 