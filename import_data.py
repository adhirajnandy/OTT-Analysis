from neo4j import GraphDatabase
import pandas as pd
import ast
from tqdm import tqdm
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neo4j connection details
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

def create_movie_or_show(tx, row):
    # Convert string lists to Python lists
    directors = ast.literal_eval(row['director']) if row['director'] != '[]' else []
    cast = ast.literal_eval(row['cast']) if row['cast'] != '[]' else []
    countries = ast.literal_eval(row['country']) if row['country'] != '[]' else []
    genres = ast.literal_eval(row['listed_in']) if row['listed_in'] != '[]' else []
    
    # Create Movie or TV Show node based on type
    if row['type'] == 'Movie':
        query = """
        MERGE (m:Movie {show_id: $show_id})
        SET m.title = $title,
            m.release_year = $release_year,
            m.rating = $rating,
            m.duration = $duration
        """
    else:
        query = """
        MERGE (t:TVShow {show_id: $show_id})
        SET t.title = $title,
            t.release_year = $release_year,
            t.rating = $rating,
            t.duration = $duration
        """
    
    tx.run(query, 
           show_id=row['show_id'],
           title=row['title'],
           release_year=row['release_year'],
           rating=row['rating'],
           duration=row['duration'])
    
    # Create and connect Director nodes
    for director in directors:
        query = """
        MERGE (d:Director {name: $name})
        WITH d
        MATCH (n {show_id: $show_id})
        MERGE (d)-[:DIRECTED]->(n)
        """
        tx.run(query, name=director, show_id=row['show_id'])
    
    # Create and connect Actor nodes
    for actor in cast:
        query = """
        MERGE (a:Actor {name: $name})
        WITH a
        MATCH (n {show_id: $show_id})
        MERGE (a)-[:ACTED_IN]->(n)
        """
        tx.run(query, name=actor, show_id=row['show_id'])
    
    # Create and connect Country nodes
    for country in countries:
        query = """
        MERGE (c:Country {name: $name})
        WITH c
        MATCH (n {show_id: $show_id})
        MERGE (n)-[:RELEASED_IN]->(c)
        """
        tx.run(query, name=country, show_id=row['show_id'])
    
    # Create and connect Genre nodes
    for genre in genres:
        query = """
        MERGE (g:Genre {name: $name})
        WITH g
        MATCH (n {show_id: $show_id})
        MERGE (n)-[:BELONGS_TO_GENRE]->(g)
        """
        tx.run(query, name=genre, show_id=row['show_id'])

def import_data(driver, csv_file):
    # Read the CSV file
    print("Reading CSV file...")
    df = pd.read_csv(csv_file)
    print(f"Found {len(df)} records to import")
    
    # Import data in batches
    with driver.session() as session:
        for _, row in tqdm(df.iterrows(), total=len(df)):
            session.execute_write(create_movie_or_show, row)
    
    print("Data import completed successfully!")

def main():
    try:
        # Create driver
        driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
        
        # Verify connection
        driver.verify_connectivity()
        print("Successfully connected to Neo4j database!")
        
        # Import data
        import_data(driver, 'netflix_titles_cleaned.csv')
        
        driver.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Please check your Neo4j Aura credentials and make sure the instance is running")

if __name__ == "__main__":
    main() 