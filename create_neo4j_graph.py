from neo4j import GraphDatabase
import pandas as pd
import os
from dotenv import load_dotenv
import ast

# Load environment variables
load_dotenv()
# Neo4j connection details
uri = os.getenv("NEO4J_URI")  # Added port number
user = os.getenv("NEO4J_USER")
password = os.getenv('NEO4J_PASSWORD')

class NetflixGraph:
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # Verify connectivity
            self.driver.verify_connectivity()
            print("Successfully connected to Neo4j")
        except Exception as e:
            print(f"Failed to connect to Neo4j: {str(e)}")
            raise
        
    def close(self):
        self.driver.close()
        
    def create_constraints(self, session):
        try:
            # Create constraints for unique nodes
            session.run("CREATE CONSTRAINT title_id IF NOT EXISTS FOR (t:Title) REQUIRE t.id IS UNIQUE")
            session.run("CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE")
            session.run("CREATE CONSTRAINT country_name IF NOT EXISTS FOR (c:Country) REQUIRE c.name IS UNIQUE")
            session.run("CREATE CONSTRAINT director_name IF NOT EXISTS FOR (d:Director) REQUIRE d.name IS UNIQUE")
            session.run("CREATE CONSTRAINT cast_name IF NOT EXISTS FOR (a:Cast) REQUIRE a.name IS UNIQUE")
            session.run("CREATE CONSTRAINT year_value IF NOT EXISTS FOR (y:Year) REQUIRE y.year IS UNIQUE")
            print("Constraints created successfully")
        except Exception as e:
            print(f"Error creating constraints: {str(e)}")
            raise
        
    def create_graph(self):
        # Read the CSV file
        df = pd.read_csv('netflix_titles_cleaned.csv')
        
        with self.driver.session() as session:
            # Create constraints
            self.create_constraints(session)
            
            # Create nodes and relationships
            for _, row in df.iterrows():
                # Create Title node
                session.run("""
                    MERGE (t:Title {id: $show_id})
                    SET t.title = $title,
                        t.type = $type,
                        t.rating = $rating,
                        t.duration = $duration
                """, show_id=row['show_id'], 
                    title=row['title'],
                    type=row['type'],
                    rating=row['rating'],
                    duration=row['duration'])
                
                # Create Year node and relationship
                if pd.notna(row['release_year']):
                    session.run("""
                        MATCH (t:Title {id: $show_id})
                        MERGE (y:Year {year: $year})
                        MERGE (t)-[:RELEASED_IN]->(y)
                    """, show_id=row['show_id'], year=row['release_year'])
                
                # Create Genre nodes and relationships
                if pd.notna(row['listed_in']):
                    try:
                        genres = ast.literal_eval(row['listed_in'])
                        for genre in genres:
                            session.run("""
                                MATCH (t:Title {id: $show_id})
                                MERGE (g:Genre {name: $genre})
                                MERGE (t)-[:HAS_GENRE]->(g)
                            """, show_id=row['show_id'], genre=genre)
                    except:
                        genres = [g.strip() for g in row['listed_in'].split(',')]
                        for genre in genres:
                            session.run("""
                                MATCH (t:Title {id: $show_id})
                                MERGE (g:Genre {name: $genre})
                                MERGE (t)-[:HAS_GENRE]->(g)
                            """, show_id=row['show_id'], genre=genre)
                
                # Create Country nodes and relationships
                if pd.notna(row['country']):
                    try:
                        countries = ast.literal_eval(row['country'])
                        for country in countries:
                            if country:  # Only create if country is not empty
                                session.run("""
                                    MATCH (t:Title {id: $show_id})
                                    MERGE (c:Country {name: $country})
                                    MERGE (t)-[:PRODUCED_IN]->(c)
                                """, show_id=row['show_id'], country=country)
                    except:
                        countries = [c.strip() for c in row['country'].split(',')]
                        for country in countries:
                            if country:  # Only create if country is not empty
                                session.run("""
                                    MATCH (t:Title {id: $show_id})
                                    MERGE (c:Country {name: $country})
                                    MERGE (t)-[:PRODUCED_IN]->(c)
                                """, show_id=row['show_id'], country=country)
                
                # Create Director nodes and relationships
                if pd.notna(row['director']):
                    try:
                        directors = ast.literal_eval(row['director'])
                        for director in directors:
                            if director:  # Only create if director is not empty
                                session.run("""
                                    MATCH (t:Title {id: $show_id})
                                    MERGE (d:Director {name: $director})
                                    MERGE (t)-[:DIRECTED_BY]->(d)
                                """, show_id=row['show_id'], director=director)
                    except:
                        directors = [d.strip() for d in row['director'].split(',')]
                        for director in directors:
                            if director:  # Only create if director is not empty
                                session.run("""
                                    MATCH (t:Title {id: $show_id})
                                    MERGE (d:Director {name: $director})
                                    MERGE (t)-[:DIRECTED_BY]->(d)
                                """, show_id=row['show_id'], director=director)
                
                # Create Cast nodes and relationships
                if pd.notna(row['cast']):
                    try:
                        cast_members = ast.literal_eval(row['cast'])
                        for cast_member in cast_members:
                            if cast_member:  # Only create if cast member is not empty
                                session.run("""
                                    MATCH (t:Title {id: $show_id})
                                    MERGE (a:Cast {name: $cast_member})
                                    MERGE (t)-[:ACTED_IN]->(a)
                                """, show_id=row['show_id'], cast_member=cast_member)
                    except:
                        cast_members = [c.strip() for c in row['cast'].split(',')]
                        for cast_member in cast_members:
                            if cast_member:  # Only create if cast member is not empty
                                session.run("""
                                    MATCH (t:Title {id: $show_id})
                                    MERGE (a:Cast {name: $cast_member})
                                    MERGE (t)-[:ACTED_IN]->(a)
                                """, show_id=row['show_id'], cast_member=cast_member)

def main():
    graph = NetflixGraph()
    try:
        print("Creating Neo4j graph...")
        graph.create_graph()
        print("Graph creation completed successfully!")
    finally:
        graph.close()

if __name__ == "__main__":
    main() 