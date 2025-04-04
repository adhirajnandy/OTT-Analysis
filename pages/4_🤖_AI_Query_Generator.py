import streamlit as st
from neo4j import GraphDatabase
import pandas as pd
import os
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime
import re
import plotly.express as px
import plotly.graph_objects as go

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
    Convert this natural language query to a Cypher query for Neo4j:
    "{user_input}"
    
    The database schema is:
    - Nodes: Movie, TVShow, Director, Actor, Country, Genre
    - Relationships: 
      - (Actor)-[:ACTED_IN]->(Movie/TVShow)
      - (Director)-[:DIRECTED]->(Movie/TVShow)
      - (Movie/TVShow)-[:RELEASED_IN]->(Country)
      - (Movie/TVShow)-[:BELONGS_TO_GENRE]->(Genre)
    
    Return only the Cypher query without any explanation or markdown formatting.
    """
    
    try:
        response = model.generate_content(prompt)
        if response.text:
            return clean_cypher_query(response.text)
        else:
            return "Error: No response generated"
    except Exception as e:
        st.error(f"Error with Gemini API: {str(e)}")
        return "MATCH (m:Movie) RETURN m LIMIT 5"  # Fallback query

def execute_query(cypher_query, neo4j):
    try:
        results = neo4j.query(cypher_query)
        if results:
            return pd.DataFrame(results)
        else:
            return None
    except Exception as e:
        st.error(f"Error executing query: {str(e)}")
        return None

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
        st.session_state.query_results = None
    
    # Example queries
    st.sidebar.header("Example Queries")
    example_queries = [
        "Show me all movies directed by Christopher Nolan",
        "Find actors who worked with Tom Cruise",
        "Find directors who worked with multiple actors",
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
                st.session_state.query_results = None  # Reset results
    
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
    if st.session_state.query_results is not None:
        st.subheader("Results:")
        if st.session_state.query_results.empty:
            st.warning("No records found for this query. Try modifying your question or using a different example query.")
        else:
            # Display the table
            st.dataframe(st.session_state.query_results)
            
            # Create visualization if possible
            if len(st.session_state.query_results.columns) >= 2:
                # If we have numeric data, create a bar chart
                if st.session_state.query_results[st.session_state.query_results.columns[1]].dtype in ['int64', 'float64']:
                    fig = px.bar(st.session_state.query_results, 
                               x=st.session_state.query_results.columns[0],
                               y=st.session_state.query_results.columns[1],
                               title=f"{st.session_state.query_results.columns[1]} by {st.session_state.query_results.columns[0]}")
                    st.plotly_chart(fig, use_container_width=True)
                
                # If we have categorical data, create a pie chart
                elif st.session_state.query_results[st.session_state.query_results.columns[1]].dtype == 'object' and len(st.session_state.query_results) <= 10:
                    fig = px.pie(st.session_state.query_results, 
                               names=st.session_state.query_results.columns[0],
                               values=st.session_state.query_results.columns[1] if st.session_state.query_results[st.session_state.query_results.columns[1]].dtype in ['int64', 'float64'] else None,
                               title=f"Distribution of {st.session_state.query_results.columns[0]}")
                    st.plotly_chart(fig, use_container_width=True)
                
                # If we have time series data, create a line chart
                elif 'year' in st.session_state.query_results.columns[0].lower() or 'date' in st.session_state.query_results.columns[0].lower():
                    fig = px.line(st.session_state.query_results, 
                                x=st.session_state.query_results.columns[0],
                                y=st.session_state.query_results.columns[1],
                                title=f"{st.session_state.query_results.columns[1]} over {st.session_state.query_results.columns[0]}")
                    st.plotly_chart(fig, use_container_width=True)
                
                # For other cases, create a scatter plot
                else:
                    fig = px.scatter(st.session_state.query_results, 
                                   x=st.session_state.query_results.columns[0],
                                   y=st.session_state.query_results.columns[1],
                                   title=f"{st.session_state.query_results.columns[1]} vs {st.session_state.query_results.columns[0]}")
                    st.plotly_chart(fig, use_container_width=True)
    
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