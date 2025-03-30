# Netflix Content Analysis Dashboard

A comprehensive analytics and recommendation system for Netflix content, built with Streamlit and Neo4j.

## 🎯 Overview

This project is a multi-page Streamlit application that provides detailed analytics and insights about Netflix content. It includes features for analyzing movies and TV shows, exploring actor and director relationships, genre analysis, and personalized movie recommendations.

## 🚀 Features

### 1. Home Dashboard
- Quick statistics about the content library
- Content type distribution (Movies vs TV Shows)
- Popular genre combinations
- Interactive filters for:
  - Years
  - Ratings
  - Genres
  - Countries
- Search functionality for movies and TV shows

### 2. Actor/Director Analysis
- Top actors and directors
- Collaboration networks
- Performance metrics
- Visualizations of relationships

### 3. Genre Analysis
- Genre distribution
- Genre combinations
- Genre trends over time
- Interactive genre visualizations

### 4. Movie Recommendations
- Personalized movie recommendations based on:
  - Genre similarity (weight: 2.0)
  - Actor overlap (weight: 1.5)
  - Director overlap (weight: 1.5)
- Interactive search interface
- Detailed movie information
- Similarity score visualization

## 🛠️ Technical Stack

- **Frontend**: Streamlit
- **Database**: Neo4j (Graph Database)
- **Data Visualization**: Plotly
- **Data Processing**: Pandas
- **Environment Management**: python-dotenv

## 📊 Data Model

The project uses a Neo4j graph database with the following main entities:
- Movies
- TV Shows
- Actors
- Directors
- Genres
- Countries

Relationships include:
- ACTED_IN
- DIRECTED
- BELONGS_TO_GENRE
- RELEASED_IN

## 🚀 Getting Started

1. **Prerequisites**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Setup**
   Create a `.env` file with your Neo4j credentials:
   ```
   NEO4J_URI=your_neo4j_uri
   NEO4J_USERNAME=your_username
   NEO4J_PASSWORD=your_password
   ```

3. **Run the Application**
   ```bash
   streamlit run Home.py
   ```

## 📈 Similarity Score Calculation

The recommendation system uses a sophisticated scoring mechanism based on multiple factors:

1. **Genre Similarity (Weight: 2.0)**
   - Counts shared genres between movies
   - Each matching genre adds 2 points

2. **Actor Overlap (Weight: 1.5)**
   - Counts actors appearing in both movies
   - Each matching actor adds 1.5 points

3. **Director Overlap (Weight: 1.5)**
   - Counts directors working on both movies
   - Each matching director adds 1.5 points

Total Score = (Genre Matches × 2.0) + (Actor Matches × 1.5) + (Director Matches × 1.5)

## 🔍 Usage

1. **Home Page**
   - View overall statistics
   - Use filters to narrow down content
   - Search for specific movies or TV shows

2. **Actor/Director Analysis**
   - Explore top performers
   - View collaboration networks
   - Analyze relationships

3. **Genre Analysis**
   - Study genre distributions
   - Discover genre combinations
   - Track genre trends

4. **Movie Recommendations**
   - Search for a movie
   - Get personalized recommendations
   - View similarity scores and details

## 📝 Future Enhancements

- User ratings and reviews integration
- Content popularity metrics
- More sophisticated recommendation algorithms
- Additional visualization options
- Export functionality for reports

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
