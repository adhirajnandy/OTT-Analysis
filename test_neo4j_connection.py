from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neo4j connection details from environment variables
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USERNAME")  # Note: Changed to match .env file
PASSWORD = os.getenv("NEO4J_PASSWORD")

# Debug print connection details (without password)
print(f"Connecting to Neo4j at: {URI}")
print(f"Using user: {USER}")

if not all([URI, USER, PASSWORD]):
    raise ValueError("Please set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD environment variables")

try:
    # Create driver
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    
    # Verify connection
    driver.verify_connectivity()
    print("Successfully connected to Neo4j database!")
    
    # Test a simple query
    with driver.session() as session:
        result = session.run("RETURN 1")
        print("Successfully executed test query!")
        
    driver.close()
    
except Exception as e:
    print(f"Failed to connect to Neo4j database: {str(e)}")
    print("Please check your Neo4j Aura credentials and make sure the instance is running") 