import pandas as pd
from neo4j import GraphDatabase
import ast
from tqdm import tqdm
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Neo4j connection details from environment variables
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

# Debug print connection details (without password)
print(f"Connecting to Neo4j at: {URI}")
print(f"Using user: {USER}")

if not all([URI, USER, PASSWORD]):
    raise ValueError("Please set NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD environment variables")

class NetflixGraph:
    def __init__(self):
        try:
            # Simplified connection settings
            self.driver = GraphDatabase.driver(
                URI,
                auth=(USER, PASSWORD),
                connection_timeout=30
            )
            # Verify connection
            self.driver.verify_connectivity()
            print("Successfully connected to Neo4j database!")
        except Exception as e:
            print(f"Failed to connect to Neo4j database: {str(e)}")
            print("Please check your Neo4j Aura credentials and make sure the instance is running")
            sys.exit(1)
        
    def close(self):
        self.driver.close()
        
    def create_constraints(self):
        try:
            with self.driver.session() as session:
                # Create constraints for uniqueness
                session.run("CREATE CONSTRAINT movie_id IF NOT EXISTS FOR (m:Movie) ON (m.show_id) IS UNIQUE")
                session.run("CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) ON (p.name) IS UNIQUE")
                session.run("CREATE CONSTRAINT country_name IF NOT EXISTS FOR (c:Country) ON (c.name) IS UNIQUE")
                session.run("CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) ON (g.name) IS UNIQUE")
                print("Successfully created constraints!")
        except Exception as e:
            print(f"Error creating constraints: {str(e)}")
            raise
    
    def create_movie_node(self, tx, row):
        try:
            # Create Movie/TV Show node
            query = """
            MERGE (m:Movie {show_id: $show_id})
            SET m.title = $title,
                m.type = $type,
                m.release_year = $release_year,
                m.rating = $rating,
                m.duration = $duration
            """
            tx.run(query, show_id=row['show_id'], 
                   title=row['title'],
                   type=row['type'],
                   release_year=row['release_year'],
                   rating=row['rating'],
                   duration=row['duration'])
            
            # Create and connect Director nodes
            directors = ast.literal_eval(row['director']) if row['director'] != '[]' else []
            for director in directors:
                query = """
                MERGE (d:Person {name: $name})
                WITH d
                MATCH (m:Movie {show_id: $show_id})
                MERGE (d)-[:DIRECTED]->(m)
                """
                tx.run(query, name=director, show_id=row['show_id'])
            
            # Create and connect Cast nodes
            cast = ast.literal_eval(row['cast']) if row['cast'] != '[]' else []
            for actor in cast:
                query = """
                MERGE (a:Person {name: $name})
                WITH a
                MATCH (m:Movie {show_id: $show_id})
                MERGE (a)-[:ACTED_IN]->(m)
                """
                tx.run(query, name=actor, show_id=row['show_id'])
            
            # Create and connect Country nodes
            countries = ast.literal_eval(row['country']) if row['country'] != '[]' else []
            for country in countries:
                query = """
                MERGE (c:Country {name: $name})
                WITH c
                MATCH (m:Movie {show_id: $show_id})
                MERGE (m)-[:PRODUCED_IN]->(c)
                """
                tx.run(query, name=country, show_id=row['show_id'])
            
            # Create and connect Genre nodes
            genres = ast.literal_eval(row['listed_in']) if row['listed_in'] != '[]' else []
            for genre in genres:
                query = """
                MERGE (g:Genre {name: $name})
                WITH g
                MATCH (m:Movie {show_id: $show_id})
                MERGE (m)-[:BELONGS_TO]->(g)
                """
                tx.run(query, name=genre, show_id=row['show_id'])
        except Exception as e:
            print(f"Error processing row {row['show_id']}: {str(e)}")
            raise

def main():
    try:
        # Read the CSV file
        print("Reading CSV file...")
        df = pd.read_csv('netflix_titles_cleaned.csv')
        print(f"Successfully read {len(df)} rows from CSV")
        
        # Initialize Neo4j graph
        graph = NetflixGraph()
        
        try:
            # Create constraints
            print("Creating constraints...")
            graph.create_constraints()
            
            # Create nodes and relationships
            print("Creating nodes and relationships...")
            with graph.driver.session() as session:
                for _, row in tqdm(df.iterrows(), total=len(df)):
                    session.execute_write(graph.create_movie_node, row)
            
            print("Graph creation completed successfully!")
            
        finally:
            graph.close()
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 