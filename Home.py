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
    
    # Sidebar Filters
    st.sidebar.header("Filters")
    
    # Content Type Filter
    content_type = st.sidebar.multiselect(
        "Content Type",
        ["Movie", "TV Show"],
        default=["Movie", "TV Show"]
    )
    
    # Get available genres for filter
    genre_query = """
    MATCH (g:Genre)
    RETURN g.name as genre
    ORDER BY g.name
    """
    genres = [row['genre'] for row in neo4j.query(genre_query)]
    
    # Genre Filter
    selected_genres = st.sidebar.multiselect(
        "Genres",
        genres,
        default=[]
    )
    
    # Year Range Filter
    year_query = """
    MATCH (m)
    WHERE m:Movie OR m:TVShow
    RETURN min(m.release_year) as min_year, max(m.release_year) as max_year
    """
    year_range = neo4j.query(year_query)[0]
    min_year = int(year_range['min_year']) if year_range['min_year'] else 1900
    max_year = int(year_range['max_year']) if year_range['max_year'] else datetime.now().year
    
    year_range = st.sidebar.slider(
        "Year Range",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
    
    # Build filter conditions
    content_type_condition = " OR ".join([f"m:{'TVShow' if content == 'TV Show' else content}" for content in content_type]) if content_type else "m:Movie OR m:TVShow"
    genre_condition = " AND ".join([f"g.name = '{genre}'" for genre in selected_genres]) if selected_genres else "true"
    
    # Display Filtered Records
    st.header("Filtered Content")
    
    # Add a search box for the filtered content
    search_term = st.text_input("Search in filtered content", "")
    
    # Modify the filtered query to include search
    filtered_query = f"""
    MATCH (m)
    WHERE ({content_type_condition})
    AND m.release_year >= {year_range[0]}
    AND m.release_year <= {year_range[1]}
    MATCH (m)-[:BELONGS_TO_GENRE]->(g:Genre)
    WHERE {genre_condition}
    AND (
        CASE 
            WHEN $search_term IS NOT NULL AND $search_term <> '' 
            THEN toLower(m.title) CONTAINS toLower($search_term)
            OR toLower(g.name) CONTAINS toLower($search_term)
            ELSE true 
        END
    )
    WITH DISTINCT m, collect(g.name) as genres
    RETURN 
        m.title as title,
        CASE WHEN m:Movie THEN 'Movie' ELSE 'TV Show' END as type,
        m.release_year as release_year,
        genres,
        m.rating as rating,
        m.duration as duration
    ORDER BY m.release_year DESC
    LIMIT 100
    """
    
    filtered_df = pd.DataFrame(neo4j.query(filtered_query, params={"search_term": search_term}))
    
    if not filtered_df.empty:
        # Convert genres list to string
        filtered_df['genres'] = filtered_df['genres'].apply(lambda x: ', '.join(x))
        
        # Display the filtered content in a table
        st.dataframe(
            filtered_df,
            column_config={
                "title": "Title",
                "type": "Type",
                "release_year": "Release Year",
                "genres": "Genres",
                "rating": "Rating",
                "duration": "Duration"
            },
            hide_index=True
        )
        
        # Show total count of filtered records
        st.info(f"Showing {len(filtered_df)} records (limited to 100)")
    else:
        st.info("No content found for the selected filters.")
    
    # Quick Stats
    st.header("Quick Statistics")
    
    # Get total movies and TV shows with filters
    content_query = f"""
    MATCH (m)
    WHERE ({content_type_condition})
    AND m.release_year >= {year_range[0]}
    AND m.release_year <= {year_range[1]}
    MATCH (m)-[:BELONGS_TO_GENRE]->(g:Genre)
    WHERE {genre_condition}
    RETURN 
        CASE WHEN m:Movie THEN 'Movie' ELSE 'TV Show' END as type,
        count(DISTINCT m) as count
    """
    content_df = pd.DataFrame(neo4j.query(content_query))
    
    # Display metrics
    col1, col2 = st.columns(2)
    with col1:
        movies_count = content_df[content_df['type'] == 'Movie']['count'].iloc[0] if not content_df.empty and 'Movie' in content_df['type'].values else 0
        st.metric("Total Movies", movies_count)
    with col2:
        tvshows_count = content_df[content_df['type'] == 'TV Show']['count'].iloc[0] if not content_df.empty and 'TV Show' in content_df['type'].values else 0
        st.metric("Total TV Shows", tvshows_count)
    
    # Node Type Distribution
    st.header("Content Type Distribution")
    if not content_df.empty:
        fig = px.pie(content_df, values='count', names='type', 
                     title='Distribution of Movies vs TV Shows')
        st.plotly_chart(fig)
    else:
        st.info("No content found for the selected filters.")
    
    # Get total actors and directors with filters
    people_query = f"""
    MATCH (m)
    WHERE {content_type_condition}
    AND m.release_year >= {year_range[0]}
    AND m.release_year <= {year_range[1]}
    MATCH (m)-[:BELONGS_TO_GENRE]->(g:Genre)
    WHERE {genre_condition}
    MATCH (m)<-[:ACTED_IN]-(a:Actor)
    WITH count(DISTINCT a) as actor_count
    MATCH (m)<-[:DIRECTED]-(d:Director)
    WITH actor_count, count(DISTINCT d) as director_count
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
    
    # Popular Genre Combinations with filters
    st.header("Popular Genre Combinations")
    genre_query = f"""
    MATCH (m)
    WHERE {content_type_condition}
    AND m.release_year >= {year_range[0]}
    AND m.release_year <= {year_range[1]}
    MATCH (m)-[:BELONGS_TO_GENRE]->(g:Genre)
    WHERE {genre_condition}
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
    else:
        st.info("No genre combinations found for the selected filters.")
    
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