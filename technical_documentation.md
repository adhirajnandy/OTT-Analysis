# Netflix Content Analysis Dashboard - Technical Documentation

## Table of Contents
1. [System Architecture](#1-system-architecture)
2. [Database Schema](#2-database-schema)
3. [API Endpoints](#3-api-endpoints)
4. [Data Models](#4-data-models)
5. [Implementation Details](#5-implementation-details)
6. [Security](#6-security)
7. [Performance Optimization](#7-performance-optimization)
8. [Deployment Guide](#8-deployment-guide)
9. [Testing](#9-testing)
10. [Maintenance](#10-maintenance)

## 1. System Architecture

### 1.1 Overview
```
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|  Streamlit UI    |<--->|  Python Backend  |<--->|  Neo4j Database  |
|                  |     |                  |     |                  |
+------------------+     +------------------+     +------------------+
```

### 1.2 Components
- **Frontend**: Streamlit-based web interface
- **Backend**: Python application with Neo4j driver
- **Database**: Neo4j graph database
- **Data Processing**: Pandas for data manipulation
- **Visualization**: Plotly for interactive charts

### 1.3 Dependencies
```python
# requirements.txt
pandas>=1.5.0
neo4j>=5.14.1
tqdm>=4.66.1
python-dotenv>=1.0.0
streamlit>=1.31.0
plotly>=5.18.0
google-generativeai>=0.3.0
```

## 2. Database Schema

### 2.1 Node Types
```cypher
// Movie Node
CREATE (m:Movie {
    title: string,
    release_year: integer,
    rating: string,
    duration: string,
    description: string
})

// TVShow Node
CREATE (t:TVShow {
    title: string,
    release_year: integer,
    rating: string,
    duration: string,
    description: string
})

// Actor Node
CREATE (a:Actor {
    name: string
})

// Director Node
CREATE (d:Director {
    name: string
})

// Genre Node
CREATE (g:Genre {
    name: string
})

// Country Node
CREATE (c:Country {
    name: string
})
```

### 2.2 Relationships
```cypher
// ACTED_IN relationship
CREATE (a:Actor)-[:ACTED_IN]->(m:Movie)

// DIRECTED relationship
CREATE (d:Director)-[:DIRECTED]->(m:Movie)

// BELONGS_TO_GENRE relationship
CREATE (m:Movie)-[:BELONGS_TO_GENRE]->(g:Genre)

// RELEASED_IN relationship
CREATE (m:Movie)-[:RELEASED_IN]->(c:Country)
```

### 2.3 Indexes and Constraints
```cypher
// Create constraints
CREATE CONSTRAINT movie_title IF NOT EXISTS
FOR (m:Movie) REQUIRE m.title IS UNIQUE

CREATE CONSTRAINT tvshow_title IF NOT EXISTS
FOR (t:TVShow) REQUIRE t.title IS UNIQUE

CREATE CONSTRAINT actor_name IF NOT EXISTS
FOR (a:Actor) REQUIRE a.name IS UNIQUE

CREATE CONSTRAINT director_name IF NOT EXISTS
FOR (d:Director) REQUIRE d.name IS UNIQUE

// Create indexes
CREATE INDEX movie_year IF NOT EXISTS
FOR (m:Movie) ON (m.release_year)

CREATE INDEX movie_rating IF NOT EXISTS
FOR (m:Movie) ON (m.rating)
```

## 3. API Endpoints

### 3.1 Neo4j Queries
```cypher
// Get movie recommendations
MATCH (selected:Movie {title: $movie})
WITH selected
MATCH (selected)-[:BELONGS_TO_GENRE]->(g:Genre)<-[:BELONGS_TO_GENRE]-(similar:Movie)
WHERE similar <> selected
WITH selected, similar, count(DISTINCT g) as genre_matches
OPTIONAL MATCH (selected)<-[:ACTED_IN]-(a:Actor)-[:ACTED_IN]->(similar)
WITH selected, similar, genre_matches, count(DISTINCT a) as actor_matches
OPTIONAL MATCH (selected)<-[:DIRECTED]-(d:Director)-[:DIRECTED]->(similar)
WITH selected, similar, 
     genre_matches * 2 as genre_score,
     actor_matches * 1.5 as actor_score,
     director_matches * 1.5 as director_score
WITH similar,
     genre_score + actor_score + director_score as total_score
ORDER BY total_score DESC
LIMIT 10
```

### 3.2 Streamlit Pages
- `Home.py`: Main dashboard
- `pages/1_🎭_Actor_Director_Analysis.py`: Actor/Director analysis
- `pages/2_🎬_Genre_Analysis.py`: Genre analysis
- `pages/3_📝_Add_New_Content.py`: Content management
- `pages/4_🤖_AI_Query_Generator.py`: AI-powered queries
- `pages/5_🎯_Movie_Recommendations.py`: Movie recommendations

## 4. Data Models

### 4.1 Movie Model
```python
class Movie:
    def __init__(self):
        self.title: str
        self.release_year: int
        self.rating: str
        self.duration: str
        self.description: str
        self.genres: List[str]
        self.actors: List[str]
        self.directors: List[str]
        self.countries: List[str]
```

### 4.2 Similarity Score Model
```python
class SimilarityScore:
    def __init__(self):
        self.genre_score: float  # weight: 2.0
        self.actor_score: float  # weight: 1.5
        self.director_score: float  # weight: 1.5
        self.total_score: float
```

## 5. Implementation Details

### 5.1 Database Connection
```python
class Neo4jConnection:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            URI, 
            auth=(USER, PASSWORD)
        )
    
    def close(self):
        self.driver.close()
    
    def query(self, query, params=None):
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]
```

### 5.2 Error Handling
```python
try:
    neo4j = Neo4jConnection()
except Exception as e:
    st.error(f"Failed to connect to Neo4j: {str(e)}")
    st.stop()
```

## 6. Security

### 6.1 Environment Variables
```bash
# .env file
NEO4J_URI=your_neo4j_uri
NEO4J_USERNAME=your_username
NEO4J_PASSWORD=your_password
```

### 6.2 Data Validation
- Input sanitization for user queries
- Parameterized queries to prevent injection
- Error handling for database operations

## 7. Performance Optimization

### 7.1 Query Optimization
- Use of indexes for faster lookups
- Efficient relationship traversal
- Limited result sets

### 7.2 Caching
- Streamlit's built-in caching
- Query result caching
- Visualization caching

## 8. Deployment Guide

### 8.1 Prerequisites
```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up Neo4j database
# Configure environment variables
```

### 8.2 Running the Application
```bash
streamlit run Home.py
```

## 9. Testing

### 9.1 Unit Tests
```python
def test_similarity_score():
    # Test similarity score calculation
    pass

def test_database_connection():
    # Test database connectivity
    pass
```

### 9.2 Integration Tests
- End-to-end workflow testing
- Database operation testing
- UI component testing

## 10. Maintenance

### 10.1 Regular Tasks
- Database backup
- Index maintenance
- Performance monitoring
- Error log review

### 10.2 Updates
- Dependency updates
- Security patches
- Feature additions
- Bug fixes

## Appendix

### A. Common Issues and Solutions
1. Database Connection Issues
   - Check Neo4j service status
   - Verify credentials
   - Check network connectivity

2. Performance Issues
   - Optimize queries
   - Check indexes
   - Monitor resource usage

3. UI Issues
   - Clear browser cache
   - Check Streamlit version
   - Verify data integrity

### B. Best Practices
1. Code Style
   - Follow PEP 8
   - Use type hints
   - Write docstrings

2. Database
   - Use parameterized queries
   - Create appropriate indexes
   - Regular maintenance

3. UI/UX
   - Responsive design
   - Clear error messages
   - Intuitive navigation 