import streamlit as st
from neo4j import GraphDatabase
import pandas as pd
import os
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime
import re
import plotly.express as px

# Load environment variables
load_dotenv()

# Neo4j connection details
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# List available models
try:
    for m in genai.list_models():
        print(f"Available model: {m.name}")
except Exception as e:
    print(f"Error listing models: {str(e)}")

# Use the text generation model
model = genai.GenerativeModel('gemini-1.5-pro')

class Neo4jConnection:
    def __init__(self):
        self.driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    
    def close(self):
        self.driver.close()
    
    def query(self, query, params=None):
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]

def clean_cypher_query(query):
    # Remove markdown code block syntax
    query = re.sub(r'```cypher\n?', '', query)
    query = re.sub(r'```\n?', '', query)
    # Remove any leading/trailing whitespace
    query = query.strip()
    return query

def generate_cypher_query(user_input):
    prompt = f"""
    You are a Neo4j Cypher query expert. Convert the following natural language question into a Cypher query.
    The query should be efficient and follow Neo4j best practices.
    
    Question: "{user_input}"
    
    Database Schema:
    Nodes:
    - Movie: {{title, release_year, rating, duration}}
    - TVShow: {{title, release_year, rating, duration}}
    - Director: {{name}}
    - Actor: {{name}}
    - Country: {{name}}
    - Genre: {{name}}
    
    Relationships:
    - (Actor)-[:ACTED_IN]->(Movie/TVShow)
    - (Director)-[:DIRECTED]->(Movie/TVShow)
    - (Movie/TVShow)-[:RELEASED_IN]->(Country)
    - (Movie/TVShow)-[:BELONGS_TO_GENRE]->(Genre)
    
    Important Rules:
    1. Return ONLY the Cypher query without any explanation or markdown formatting
    2. Use parameterized queries where appropriate
    3. Include LIMIT clauses to prevent large result sets
    4. Use proper indexing hints when possible
    5. Include ORDER BY clauses for better readability
    6. Use meaningful variable names
    
    Example:
    Question: "Show me all movies directed by Christopher Nolan"
    Response: MATCH (d:Director {{name: 'Christopher Nolan'}})-[:DIRECTED]->(m:Movie) RETURN m.title as title, m.release_year as year, m.rating as rating ORDER BY m.release_year DESC LIMIT 10
    
    Now, generate the Cypher query for the given question:
    """
    
    try:
        response = model.generate_content(prompt)
        if response.text:
            query = clean_cypher_query(response.text)
            # Basic validation
            if not query.startswith("MATCH"):
                return "MATCH (m:Movie) RETURN m LIMIT 5"  # Fallback query
            return query
        else:
            return "MATCH (m:Movie) RETURN m LIMIT 5"  # Fallback query
    except Exception as e:
        st.error(f"Error with Gemini API: {str(e)}")
        return "MATCH (m:Movie) RETURN m LIMIT 5"  # Fallback query

def execute_query(cypher_query, neo4j):
    try:
        results = neo4j.query(cypher_query)
        if results:
            return pd.DataFrame(results)
        else:
            return pd.DataFrame()  # Return empty DataFrame instead of None
    except Exception as e:
        st.error(f"Error executing query: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame instead of None

def main():
    st.title("🤖 AI Query Generator")
    st.write("Ask questions about the Netflix database in natural language, and I'll convert them to Cypher queries!")
    
    # Check for API key
    if not GOOGLE_API_KEY:
        st.error("Please set your GOOGLE_API_KEY in the .env file")
        st.stop()
    
    # Initialize Neo4j connection
    try:
        neo4j = Neo4jConnection()
    except Exception as e:
        st.error(f"Failed to connect to Neo4j: {str(e)}")
        st.stop()
    
    # Initialize session state
    if 'generated_query' not in st.session_state:
        st.session_state.generated_query = ""
    if 'query_results' not in st.session_state:
        st.session_state.query_results = pd.DataFrame()
    
    # Example queries
    st.sidebar.header("Example Queries")
    example_queries = [
        "Show me all movies directed by Christopher Nolan",
        "Find actors who worked with Tom Cruise",
        "List all action movies released in 2020",
        "Show me the most popular genres in India",
        "Find directors who worked with multiple actors",
        "What are the highest rated movies from 2023?",
        "Show me movies that combine Action and Drama genres",
        "Which actors have worked with the most directors?",
        "What are the most common genre combinations?",
        "Find movies released in multiple countries"
    ]
    
    for query in example_queries:
        if st.sidebar.button(query):
            st.session_state.user_query = query
    
    # User input
    user_query = st.text_area("Enter your question about the Netflix database", 
                             value=st.session_state.get('user_query', ''))
    
    # Generate Query Button
    if st.button("Generate Cypher Query"):
        if user_query:
            with st.spinner("Generating Cypher query..."):
                # Generate Cypher query
                st.session_state.generated_query = generate_cypher_query(user_query)
                st.session_state.query_results = pd.DataFrame()  # Reset results
    
    # Display and edit generated query
    if st.session_state.generated_query:
        st.subheader("Generated Cypher Query:")
        st.session_state.generated_query = st.text_area(
            "Edit the query if needed:",
            value=st.session_state.generated_query,
            height=150
        )
        
        # Execute Query Button
        if st.button("Execute Query"):
            with st.spinner("Executing query..."):
                st.session_state.query_results = execute_query(st.session_state.generated_query, neo4j)
    
    # Display results
    if not st.session_state.query_results.empty:
        st.subheader("Results:")
        st.dataframe(st.session_state.query_results)
        
        # Try to create a visualization if possible
        if len(st.session_state.query_results.columns) >= 2:
            try:
                fig = px.bar(st.session_state.query_results, 
                           x=st.session_state.query_results.columns[0],
                           y=st.session_state.query_results.columns[1])
                st.plotly_chart(fig, use_container_width=True)
            except:
                pass
    
    # Schema information
    with st.expander("View Database Schema"):
        st.markdown("""
        ### Node Types:
        - **Movie**: {title, release_year, rating, duration}
        - **TVShow**: {title, release_year, rating, duration}
        - **Director**: {name}
        - **Actor**: {name}
        - **Country**: {name}
        - **Genre**: {name}
        
        ### Relationships:
        - (Actor)-[:ACTED_IN]->(Movie/TVShow)
        - (Director)-[:DIRECTED]->(Movie/TVShow)
        - (Movie/TVShow)-[:RELEASED_IN]->(Country)
        - (Movie/TVShow)-[:BELONGS_TO_GENRE]->(Genre)
        """)
    
    # Close Neo4j connection
    neo4j.close()

if __name__ == "__main__":
    main() 