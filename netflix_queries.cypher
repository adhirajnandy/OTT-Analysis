// Basic Title Information
// Find all movies (excluding TV shows)
MATCH (t:Title)
WHERE t.type = 'Movie'
RETURN t.title, t.rating, t.duration
LIMIT 10;

// Find TV shows with less than 4 seasons
MATCH (t:Title)
WHERE t.type = 'TV Show'
WITH t, TOINTEGER(REPLACE(t.duration, ' Seasons', '')) as seasons
WHERE seasons < 4
RETURN t.title, t.rating, t.duration
ORDER BY seasons;

// Find movies by specific cast member
MATCH (t:Title)-[:ACTED_IN]->(a:Cast)
WHERE a.name = 'Alan Marriott'
RETURN t.title, t.type, t.rating, t.duration
ORDER BY t.title;

// Genre Analysis
// Find most common genres
MATCH (g:Genre)<-[:HAS_GENRE]-(t:Title)
RETURN g.name as genre, COUNT(*) as count
ORDER BY count DESC
LIMIT 10;

// Director Analysis
// Find directors who have directed the most content
MATCH (d:Director)<-[:DIRECTED_BY]-(t:Title)
RETURN d.name as director, COUNT(*) as movie_count
ORDER BY movie_count DESC
LIMIT 10;

// Actor Analysis
// Find actors who have appeared in the most content
MATCH (a:Cast)<-[:ACTED_IN]-(t:Title)
RETURN a.name as actor, COUNT(*) as appearance_count
ORDER BY appearance_count DESC
LIMIT 10;

// Country Analysis
// Find countries with the most Netflix content
MATCH (c:Country)<-[:PRODUCED_IN]-(t:Title)
RETURN c.name as country, COUNT(*) as content_count
ORDER BY content_count DESC
LIMIT 10;

// Year Analysis
// Find content distribution by year
MATCH (t:Title)-[:RELEASED_IN]->(y:Year)
RETURN y.year as year, COUNT(*) as content_count
ORDER BY year DESC
LIMIT 10;

// Complex Queries
// Find movies with specific genre and rating
MATCH (t:Title)-[:HAS_GENRE]->(g:Genre)
WHERE t.type = 'Movie' AND g.name = 'Action' AND t.rating = 'TV-MA'
RETURN t.title, t.duration
LIMIT 10;

// Find actors who worked with specific directors
MATCH (t:Title)-[:DIRECTED_BY]->(d:Director)
MATCH (t)-[:ACTED_IN]->(a:Cast)
WHERE d.name = 'Martin Scorsese'
RETURN DISTINCT a.name as actor
LIMIT 10;

// Find content by country and genre
MATCH (t:Title)-[:PRODUCED_IN]->(c:Country)
MATCH (t)-[:HAS_GENRE]->(g:Genre)
WHERE c.name = 'United States' AND g.name = 'Drama'
RETURN t.title, t.type, t.rating
LIMIT 10;

// Relationship Analysis
// Find movies with multiple genres
MATCH (t:Title)-[:HAS_GENRE]->(g:Genre)
WHERE t.type = 'Movie'
WITH t, COUNT(g) as genre_count
WHERE genre_count > 2
RETURN t.title, genre_count
ORDER BY genre_count DESC
LIMIT 10;

// Find international collaborations
MATCH (t:Title)-[:PRODUCED_IN]->(c:Country)
WITH t, COUNT(c) as country_count
WHERE country_count > 1
RETURN t.title, country_count
ORDER BY country_count DESC
LIMIT 10;

// Content Duration Analysis
// Find average duration by genre
MATCH (t:Title)-[:HAS_GENRE]->(g:Genre)
WHERE t.type = 'Movie'
WITH g.name as genre, AVG(TOINTEGER(REPLACE(t.duration, ' min', ''))) as avg_duration
RETURN genre, ROUND(avg_duration) as avg_minutes
ORDER BY avg_minutes DESC
LIMIT 10;

// Rating Distribution
// Find rating distribution across different types of content
MATCH (t:Title)
RETURN t.type, t.rating, COUNT(*) as count
ORDER BY t.type, t.rating;

// Additional Analysis Queries
// Find TV shows with most seasons
MATCH (t:Title)
WHERE t.type = 'TV Show'
RETURN t.title, t.duration
ORDER BY t.duration DESC
LIMIT 10;

// Find content by year range
MATCH (t:Title)-[:RELEASED_IN]->(y:Year)
WHERE y.year >= 2020 AND y.year <= 2023
RETURN y.year, COUNT(*) as count
ORDER BY y.year;

// Find directors who work across multiple genres
MATCH (d:Director)<-[:DIRECTED_BY]-(t:Title)-[:HAS_GENRE]->(g:Genre)
WITH d.name as director, COUNT(DISTINCT g.name) as genre_count
WHERE genre_count > 2
RETURN director, genre_count
ORDER BY genre_count DESC
LIMIT 10;

// Find actors who appear in both movies and TV shows
MATCH (a:Cast)<-[:ACTED_IN]-(t:Title)
WITH a.name as actor, COLLECT(DISTINCT t.type) as content_types
WHERE size(content_types) > 1
RETURN actor, content_types
LIMIT 10;

// Find most common genre combinations
MATCH (t:Title)-[:HAS_GENRE]->(g:Genre)
WHERE t.type = 'Movie'
WITH t.title as movie, COLLECT(g.name) as genres
WITH genres, COUNT(*) as count
ORDER BY count DESC
LIMIT 10; 