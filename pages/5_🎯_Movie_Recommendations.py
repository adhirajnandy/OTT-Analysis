import streamlit as st
from neo4j import GraphDatabase
import pandas as pd
import os
from dotenv import load_dotenv
import plotly.express as px

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
        page_title="Movie Recommendations",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 Movie Recommendations")
    st.write("Get personalized movie recommendations based on your favorite movies!")
    
    # Initialize Neo4j connection
    try:
        neo4j = Neo4jConnection()
    except Exception as e:
        st.error(f"Failed to connect to Neo4j: {str(e)}")
        st.stop()
    
    # Get list of all movies for search
    movies_query = """
    MATCH (m:Movie)
    RETURN m.title as title
    ORDER BY m.title
    """
    movies = [m['title'] for m in neo4j.query(movies_query)]
    
    # Movie search
    search_query = st.text_input(
        "Search for a movie:",
        placeholder="Type a movie title...",
        help="Start typing to search for movies. The search is case-insensitive."
    )
    
    # Filter movies based on search query
    if search_query:
        filtered_movies = [m for m in movies if search_query.lower() in m.lower()]
        if filtered_movies:
            selected_movie = st.selectbox(
                "Select from matching movies:",
                options=filtered_movies,
                help="Choose a movie from the matching results to get recommendations."
            )
        else:
            st.info("No movies found matching your search.")
            selected_movie = None
    else:
        selected_movie = None
    
    if selected_movie:
        # Get recommendations based on:
        # 1. Same genres
        # 2. Same actors
        # 3. Same directors
        # 4. Similar release years
        recommendations_query = """
        MATCH (selected:Movie {title: $movie})
        WITH selected
        
        // Get movies with same genres
        MATCH (selected)-[:BELONGS_TO_GENRE]->(g:Genre)<-[:BELONGS_TO_GENRE]-(similar:Movie)
        WHERE similar <> selected
        WITH selected, similar, count(DISTINCT g) as genre_matches
        
        // Get movies with same actors
        OPTIONAL MATCH (selected)<-[:ACTED_IN]-(a:Actor)-[:ACTED_IN]->(similar)
        WITH selected, similar, genre_matches, count(DISTINCT a) as actor_matches
        
        // Get movies with same directors
        OPTIONAL MATCH (selected)<-[:DIRECTED]-(d:Director)-[:DIRECTED]->(similar)
        WITH selected, similar, genre_matches, actor_matches, count(DISTINCT d) as director_matches
        
        // Calculate similarity score
        WITH selected, similar, 
             genre_matches * 2 as genre_score,
             actor_matches * 1.5 as actor_score,
             director_matches * 1.5 as director_score
        
        // Calculate total score and get movie details
        WITH similar,
             genre_score + actor_score + director_score as total_score
        ORDER BY total_score DESC
        LIMIT 10
        RETURN 
            similar.title as title,
            similar.release_year as year,
            similar.rating as rating,
            similar.duration as duration,
            total_score as similarity_score
        """
        
        recommendations = neo4j.query(recommendations_query, {'movie': selected_movie})
        
        if recommendations:
            st.subheader("Recommended Movies")
            
            # Create a DataFrame for better display
            df = pd.DataFrame(recommendations)
            
            # Display recommendations in a table with similarity scores
            st.dataframe(
                df.style.format({
                    'similarity_score': '{:.1f}',
                    'year': '{:.0f}'
                }),
                hide_index=True
            )
            
            # Show a bar chart of similarity scores
            fig = px.bar(
                df,
                x='title',
                y='similarity_score',
                title='Similarity Scores of Recommended Movies',
                labels={'title': 'Movie Title', 'similarity_score': 'Similarity Score'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig)
            
            # Show additional details about the selected movie
            st.subheader(f"About {selected_movie}")
            movie_details_query = """
            MATCH (m:Movie {title: $movie})
            OPTIONAL MATCH (m)-[:BELONGS_TO_GENRE]->(g:Genre)
            OPTIONAL MATCH (m)<-[:ACTED_IN]-(a:Actor)
            OPTIONAL MATCH (m)<-[:DIRECTED]-(d:Director)
            RETURN 
                m.title as title,
                m.release_year as year,
                m.rating as rating,
                m.duration as duration,
                collect(DISTINCT g.name) as genres,
                collect(DISTINCT a.name) as actors,
                collect(DISTINCT d.name) as directors
            """
            
            movie_details = neo4j.query(movie_details_query, {'movie': selected_movie})[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Release Year:** {movie_details['year']}")
                st.write(f"**Rating:** {movie_details['rating']}")
                st.write(f"**Duration:** {movie_details['duration']}")
            with col2:
                st.write("**Genres:**")
                for genre in movie_details['genres']:
                    st.write(f"- {genre}")
            
            st.write("**Top Actors:**")
            for actor in movie_details['actors'][:5]:
                st.write(f"- {actor}")
            
            st.write("**Directors:**")
            for director in movie_details['directors']:
                st.write(f"- {director}")
        else:
            st.info("No recommendations found for this movie.")
    
    # Close Neo4j connection
    neo4j.close()

if __name__ == "__main__":
    main() 