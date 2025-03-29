from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neo4j connection details from environment variables
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

def create_schema(driver):
    with driver.session() as session:
        # Create constraints for uniqueness
        print("Creating constraints...")
        session.run("CREATE CONSTRAINT movie_title IF NOT EXISTS FOR (m:Movie) REQUIRE m.title IS UNIQUE")
        session.run("CREATE CONSTRAINT tvshow_title IF NOT EXISTS FOR (t:TVShow) REQUIRE t.title IS UNIQUE")
        session.run("CREATE CONSTRAINT director_name IF NOT EXISTS FOR (d:Director) REQUIRE d.name IS UNIQUE")
        session.run("CREATE CONSTRAINT actor_name IF NOT EXISTS FOR (a:Actor) REQUIRE a.name IS UNIQUE")
        session.run("CREATE CONSTRAINT country_name IF NOT EXISTS FOR (c:Country) REQUIRE c.name IS UNIQUE")
        session.run("CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE")
        
        # Create indexes for better query performance
        print("Creating indexes...")
        # Movie indexes
        session.run("CREATE INDEX movie_year IF NOT EXISTS FOR (m:Movie) ON (m.release_year)")
        session.run("CREATE INDEX movie_rating IF NOT EXISTS FOR (m:Movie) ON (m.rating)")
        session.run("CREATE INDEX movie_duration IF NOT EXISTS FOR (m:Movie) ON (m.duration)")
        
        # TV Show indexes
        session.run("CREATE INDEX tvshow_year IF NOT EXISTS FOR (t:TVShow) ON (t.release_year)")
        session.run("CREATE INDEX tvshow_rating IF NOT EXISTS FOR (t:TVShow) ON (t.rating)")
        session.run("CREATE INDEX tvshow_duration IF NOT EXISTS FOR (t:TVShow) ON (t.duration)")
        
        print("Schema creation completed successfully!")

def main():
    try:
        # Create driver
        driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
        
        # Verify connection
        driver.verify_connectivity()
        print("Successfully connected to Neo4j database!")
        
        # Create schema
        create_schema(driver)
        
        driver.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Please check your Neo4j Aura credentials and make sure the instance is running")

if __name__ == "__main__":
    main() 