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
    st.title("🎭 Actor & Director Analysis")
    
    # Initialize Neo4j connection
    neo4j = Neo4jConnection()
    
    # Top Actors Section
    st.header("Top Actors")
    
    # Top actors by movie count
    actor_query = """
    MATCH (a:Actor)-[:ACTED_IN]->(n)
    RETURN a.name as name, count(n) as movie_count
    ORDER BY movie_count DESC
    LIMIT 10
    """
    actor_data = neo4j.query(actor_query)
    actor_df = pd.DataFrame(actor_data)
    
    # Create horizontal bar chart
    fig = px.bar(actor_df, x='movie_count', y='name', orientation='h', 
                 title='Top 10 Actors by Number of Movies')
    st.plotly_chart(fig, use_container_width=True)
    
    # Actor collaboration network
    st.subheader("Actor Collaboration Network")
    collab_query = """
    MATCH (a1:Actor)-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(a2:Actor)
    WHERE a1.name < a2.name
    RETURN a1.name as actor1, a2.name as actor2, count(m) as collaborations
    ORDER BY collaborations DESC
    LIMIT 10
    """
    collab_data = neo4j.query(collab_query)
    collab_df = pd.DataFrame(collab_data)
    
    # Create heatmap-like visualization
    fig = go.Figure(data=[go.Table(
        header=dict(values=['Actor 1', 'Actor 2', 'Collaborations'],
                   fill_color='paleturquoise',
                   align='left'),
        cells=dict(values=[collab_df['actor1'], collab_df['actor2'], collab_df['collaborations']],
                  fill_color='lavender',
                  align='left'))
    ])
    st.plotly_chart(fig, use_container_width=True)
    
    # Top Directors Section
    st.header("Top Directors")
    
    # Top directors by movie count
    director_query = """
    MATCH (d:Director)-[:DIRECTED]->(n)
    RETURN d.name as name, count(n) as movie_count
    ORDER BY movie_count DESC
    LIMIT 10
    """
    director_data = neo4j.query(director_query)
    director_df = pd.DataFrame(director_data)
    
    # Create pie chart for top directors
    fig = px.pie(director_df, values='movie_count', names='name', 
                 title='Top 10 Directors by Number of Movies')
    st.plotly_chart(fig, use_container_width=True)
    
    # Director-Actor collaborations
    st.subheader("Director-Actor Collaborations")
    dir_actor_query = """
    MATCH (d:Director)-[:DIRECTED]->(m:Movie)<-[:ACTED_IN]-(a:Actor)
    RETURN d.name as director, a.name as actor, count(m) as collaborations
    ORDER BY collaborations DESC
    LIMIT 10
    """
    dir_actor_data = neo4j.query(dir_actor_query)
    dir_actor_df = pd.DataFrame(dir_actor_data)
    
    # Create scatter plot
    fig = px.scatter(dir_actor_df, x='director', y='actor', 
                     size='collaborations', title='Director-Actor Collaborations')
    st.plotly_chart(fig, use_container_width=True)
    
    # Close Neo4j connection
    neo4j.close()

if __name__ == "__main__":
    main() 