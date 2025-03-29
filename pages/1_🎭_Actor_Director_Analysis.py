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
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

class Neo4jConnection:
    def __init__(self):
        self.driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    
    def close(self):
        self.driver.close()
    
    def query(self, query, params=None):
        with self.driver.session() as session:
            result = session.run(query, params or {})
            records = []
            for record in result:
                record_dict = {}
                for key, value in record.items():
                    if hasattr(value, 'items'):  # If it's a Node or Relationship
                        record_dict[key] = dict(value.items())
                    else:
                        record_dict[key] = value
                records.append(record_dict)
            return records

def main():
    st.title("🎭 Actor & Director Analysis")
    
    # Initialize Neo4j connection
    neo4j = Neo4jConnection()
    
    # Add a custom query section
    st.header("Custom Movie Query")
    director_name = st.text_input("Enter Director Name (e.g., Christopher Nolan)")
    
    if director_name:
        movies_query = """
        MATCH (d:Director {name: $director})-[:DIRECTED]->(m:Movie)
        RETURN m.title as title, m.release_year as year, m.rating as rating, m.duration as duration
        ORDER BY m.release_year DESC
        LIMIT 5
        """
        movies_data = neo4j.query(movies_query, {'director': director_name})
        movies_df = pd.DataFrame(movies_data)
        
        if not movies_df.empty:
            # Create a styled table
            fig = go.Figure(data=[go.Table(
                header=dict(
                    values=['Title', 'Year', 'Rating', 'Duration (min)'],
                    fill_color='#262730',
                    font=dict(color='#FAFAFA', size=14),
                    align=['left', 'center', 'center', 'center'],
                    height=40
                ),
                cells=dict(
                    values=[movies_df['title'], movies_df['year'], movies_df['rating'], movies_df['duration']],
                    fill_color='#1E1E1E',
                    font=dict(color='#FAFAFA', size=12),
                    align=['left', 'center', 'center', 'center'],
                    height=35
                ))
            ])
            
            # Update layout
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#FAFAFA',
                height=300,
                margin=dict(l=20, r=20, t=60, b=20),
                showlegend=False,
                title=dict(
                    text=f"Latest Movies by {director_name}",
                    x=0.5,
                    y=0.98,
                    xanchor='center',
                    yanchor='top',
                    font=dict(size=16, color='#FAFAFA')
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No movies found for director {director_name}")
    
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
        header=dict(
            values=['Actor 1', 'Actor 2', 'Collaborations'],
            fill_color='#262730',  # Dark background for header
            font=dict(color='#FAFAFA', size=14),  # Larger font for header
            align=['left', 'left', 'center'],  # Center align the Collaborations column
            height=40  # Taller header
        ),
        cells=dict(
            values=[collab_df['actor1'], collab_df['actor2'], collab_df['collaborations']],
            fill_color='#1E1E1E',  # Slightly lighter dark background for cells
            font=dict(color='#FAFAFA', size=12),  # Slightly smaller font for cells
            align=['left', 'left', 'center'],  # Center align the Collaborations column
            height=35  # Taller cells
        ))
    ])
    
    # Update layout for dark theme
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#FAFAFA',
        height=500,  # Increased height
        margin=dict(l=20, r=20, t=60, b=20),  # Increased top margin to accommodate title
        showlegend=False
    )
    
    # Add a title to the table
    fig.update_layout(
        title=dict(
            text="Top Actor Collaborations",
            x=0.5,  # Center the title
            y=0.98,  # Moved title higher up
            xanchor='center',
            yanchor='top',
            font=dict(size=16, color='#FAFAFA')
        )
    )
    
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