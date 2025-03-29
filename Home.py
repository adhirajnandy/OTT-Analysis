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
    try:
        neo4j = Neo4jConnection()
    except Exception as e:
        st.error(f"Failed to connect to Neo4j: {str(e)}")
        st.stop()
    
    # Search Bar
    st.header("🔍 Search Content")
    search_query = st.text_input("Search for movies or TV shows by title:", placeholder="Enter title...")
    
    if search_query:
        search_results_query = """
        MATCH (m)
        WHERE (m:Movie OR m:TVShow)
        AND toLower(m.title) CONTAINS toLower($search_query)
        RETURN 
            CASE WHEN m:Movie THEN 'Movie' ELSE 'TV Show' END as type,
            m.title as title,
            m.release_year as year,
            m.rating as rating,
            m.duration as duration
        ORDER BY m.release_year DESC
        LIMIT 10
        """
        
        search_results = neo4j.query(search_results_query, {'search_query': search_query})
        if search_results:
            st.subheader("Search Results")
            for result in search_results:
                with st.expander(f"{result['type']}: {result['title']} ({result['year']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Rating:** {result['rating']}")
                        st.write(f"**Duration:** {result['duration']}")
                    with col2:
                        st.write(f"**Type:** {result['type']}")
                        st.write(f"**Year:** {result['year']}")
        else:
            st.info("No results found for your search.")
    
    # Filters Section in Sidebar
    st.sidebar.header("🔍 Filters")
    
    # Year Range Filter
    year_query = """
    MATCH (m:Movie)
    RETURN DISTINCT m.release_year as year
    ORDER BY year
    """
    years = [str(y['year']) for y in neo4j.query(year_query) if y['year']]
    selected_years = st.sidebar.multiselect(
        "Select Years",
        options=years,
        default=[],
        help="Select one or more years. Leave empty to show all years."
    )
    
    # Rating Filter
    rating_query = """
    MATCH (m:Movie)
    RETURN DISTINCT m.rating as rating
    ORDER BY rating
    """
    ratings = [r['rating'] for r in neo4j.query(rating_query) if r['rating']]
    selected_ratings = st.sidebar.multiselect(
        "Select Ratings",
        options=ratings,
        default=[],
        help="Select one or more ratings. Leave empty to show all ratings."
    )
    
    # Genre Filter
    genre_query = """
    MATCH (g:Genre)
    RETURN g.name as genre
    ORDER BY genre
    """
    genres = [g['genre'] for g in neo4j.query(genre_query)]
    selected_genres = st.sidebar.multiselect(
        "Select Genres",
        options=genres,
        default=[],
        help="Select one or more genres. Leave empty to show all genres."
    )
    
    # Country Filter
    country_query = """
    MATCH (c:Country)
    RETURN c.name as country
    ORDER BY country
    """
    countries = [c['country'] for c in neo4j.query(country_query)]
    selected_countries = st.sidebar.multiselect(
        "Select Countries",
        options=countries,
        default=[],
        help="Select one or more countries. Leave empty to show all countries."
    )
    
    # Quick Stats with Filters
    st.header("Quick Statistics")
    
    # Get filtered content counts
    content_query = """
    MATCH (m)
    WHERE (m:Movie OR m:TVShow)
    AND (size($years) = 0 OR m.release_year IN [y IN $years | toInteger(y)])
    AND (size($ratings) = 0 OR m.rating IN $ratings)
    AND (size($genres) = 0 OR EXISTS {
        MATCH (m)-[:BELONGS_TO_GENRE]->(g:Genre)
        WHERE g.name IN $genres
    })
    AND (size($countries) = 0 OR EXISTS {
        MATCH (m)-[:RELEASED_IN]->(c:Country)
        WHERE c.name IN $countries
    })
    RETURN 
        CASE WHEN m:Movie THEN 'Movie' ELSE 'TV Show' END as type,
        count(*) as count
    """
    
    content_df = pd.DataFrame(neo4j.query(content_query, {
        'years': selected_years,
        'ratings': selected_ratings,
        'genres': selected_genres,
        'countries': selected_countries
    }))
    
    # Display metrics
    col1, col2 = st.columns(2)
    with col1:
        movies_df = content_df[content_df['type'] == 'Movie']
        movies_count = movies_df['count'].iloc[0] if not movies_df.empty else 0
        st.metric("Total Movies", movies_count)
    with col2:
        tvshows_df = content_df[content_df['type'] == 'TV Show']
        tvshows_count = tvshows_df['count'].iloc[0] if not tvshows_df.empty else 0
        st.metric("Total TV Shows", tvshows_count)
    
    # Node Type Distribution
    st.header("Content Type Distribution")
    if not content_df.empty:
        fig = px.pie(content_df, values='count', names='type', 
                     title='Distribution of Movies vs TV Shows')
        st.plotly_chart(fig)
    else:
        st.info("No content found for the selected filters.")
    
    # Get filtered actors and directors
    people_query = """
    MATCH (a:Actor)-[:ACTED_IN]->(m:Movie)
    WHERE (size($years) = 0 OR m.release_year IN [y IN $years | toInteger(y)])
    AND (size($ratings) = 0 OR m.rating IN $ratings)
    AND (size($genres) = 0 OR EXISTS {
        MATCH (m)-[:BELONGS_TO_GENRE]->(g:Genre)
        WHERE g.name IN $genres
    })
    AND (size($countries) = 0 OR EXISTS {
        MATCH (m)-[:RELEASED_IN]->(c:Country)
        WHERE c.name IN $countries
    })
    WITH count(DISTINCT a) as actor_count
    MATCH (d:Director)-[:DIRECTED]->(m:Movie)
    WHERE (size($years) = 0 OR m.release_year IN [y IN $years | toInteger(y)])
    AND (size($ratings) = 0 OR m.rating IN $ratings)
    AND (size($genres) = 0 OR EXISTS {
        MATCH (m)-[:BELONGS_TO_GENRE]->(g:Genre)
        WHERE g.name IN $genres
    })
    AND (size($countries) = 0 OR EXISTS {
        MATCH (m)-[:RELEASED_IN]->(c:Country)
        WHERE c.name IN $countries
    })
    WITH actor_count, count(DISTINCT d) as director_count
    RETURN actor_count, director_count
    """
    
    people_df = pd.DataFrame(neo4j.query(people_query, {
        'years': selected_years,
        'ratings': selected_ratings,
        'genres': selected_genres,
        'countries': selected_countries
    }))
    
    # Display metrics for people
    col1, col2 = st.columns(2)
    with col1:
        actors_count = people_df['actor_count'].iloc[0] if not people_df.empty else 0
        st.metric("Total Actors", actors_count)
    with col2:
        directors_count = people_df['director_count'].iloc[0] if not people_df.empty else 0
        st.metric("Total Directors", directors_count)
    
    # Popular Genre Combinations with Filters
    st.header("Popular Genre Combinations")
    genre_query = """
    MATCH (m:Movie)-[:BELONGS_TO_GENRE]->(g:Genre)
    WHERE (size($years) = 0 OR m.release_year IN [y IN $years | toInteger(y)])
    AND (size($ratings) = 0 OR m.rating IN $ratings)
    AND (size($countries) = 0 OR EXISTS {
        MATCH (m)-[:RELEASED_IN]->(c:Country)
        WHERE c.name IN $countries
    })
    WITH m, collect(g.name) as genres
    RETURN genres, count(*) as count
    ORDER BY count DESC
    LIMIT 10
    """
    
    genre_df = pd.DataFrame(neo4j.query(genre_query, {
        'years': selected_years,
        'ratings': selected_ratings,
        'countries': selected_countries
    }))
    
    if not genre_df.empty:
        # Convert list of genres to string for visualization
        genre_df['genres'] = genre_df['genres'].apply(lambda x: ' + '.join(x))
        
        # Create pie chart
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