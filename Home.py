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
    st.set_page_config(
        page_title="Netflix Analysis Dashboard",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 Netflix Content Analysis Dashboard")
    
    # Initialize Neo4j connection
    neo4j = Neo4jConnection()
    
    # Overview section
    st.header("Database Overview")
    
    # Get counts of different node types
    counts_query = """
    MATCH (n)
    RETURN labels(n)[0] as type, count(n) as count
    ORDER BY count DESC
    """
    counts = neo4j.query(counts_query)
    counts_df = pd.DataFrame(counts)
    
    # Create pie chart for node distribution
    fig = px.pie(counts_df, values='count', names='type', title='Node Types Distribution')
    st.plotly_chart(fig, use_container_width=True)
    
    # Display relationship counts
    rel_counts_query = """
    MATCH ()-[r]->()
    RETURN type(r) as type, count(r) as count
    ORDER BY count DESC
    """
    rel_counts = neo4j.query(rel_counts_query)
    rel_counts_df = pd.DataFrame(rel_counts)
    
    # Create donut chart for relationship distribution
    fig = px.pie(rel_counts_df, values='count', names='type', title='Relationship Types Distribution', hole=0.4)
    st.plotly_chart(fig, use_container_width=True)
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        movie_count = counts_df[counts_df['type'] == 'Movie']['count'].iloc[0]
        st.metric("Total Movies", movie_count)
    
    with col2:
        actor_count = counts_df[counts_df['type'] == 'Actor']['count'].iloc[0]
        st.metric("Total Actors", actor_count)
    
    with col3:
        director_count = counts_df[counts_df['type'] == 'Director']['count'].iloc[0]
        st.metric("Total Directors", director_count)
    
    # Close Neo4j connection
    neo4j.close()

if __name__ == "__main__":
    main() 