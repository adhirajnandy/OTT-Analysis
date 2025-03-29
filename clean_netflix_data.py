import pandas as pd
import numpy as np
import ast
import re

def clean_netflix_data():
    # Read the CSV file
    print("Reading the Netflix titles dataset...")
    df = pd.read_csv('netflix_titles.csv')
    
    # Display initial information
    print("\nInitial dataset info:")
    print(df.info())
    print("\nMissing values:")
    print(df.isnull().sum())
    
    # Clean the data
    print("\nCleaning the data...")
    
    # Handle missing values
    df['director'].fillna('No director listed', inplace=True)
    df['cast'].fillna('No cast listed', inplace=True)
    df['country'].fillna('No country listed', inplace=True)
    df['rating'].fillna('No rating listed', inplace=True)
    df['duration'].fillna('No duration listed', inplace=True)
    
    # Convert string columns to lists
    def convert_to_list(x):
        if pd.isna(x) or x == 'No director listed' or x == 'No cast listed' or x == 'No country listed':
            return []
        # Split by comma and clean each item
        return [item.strip() for item in str(x).split(',')]
    
    # Apply conversion to specified columns
    df['director'] = df['director'].apply(convert_to_list)
    df['cast'] = df['cast'].apply(convert_to_list)
    df['country'] = df['country'].apply(convert_to_list)
    df['listed_in'] = df['listed_in'].apply(convert_to_list)
    
    # Clean up duration column
    def clean_duration(row):
        duration = str(row['duration'])
        if duration == 'No duration listed':
            return None
        
        if row['type'] == 'TV Show':
            # Extract number of seasons for TV Shows
            seasons = re.search(r'(\d+)\s*Season', duration, re.IGNORECASE)
            if seasons:
                return int(seasons.group(1))
            return None
        else:
            # For movies, extract minutes
            minutes = re.search(r'(\d+)\s*min', duration, re.IGNORECASE)
            if minutes:
                return int(minutes.group(1))
            return None
    
    df['duration'] = df.apply(clean_duration, axis=1)
    
    # Drop description and date_added columns
    df = df.drop(['description', 'date_added'], axis=1)
    
    # Save the cleaned data
    print("\nSaving cleaned data...")
    df.to_csv('netflix_titles_cleaned.csv', index=False)
    
    print("\nCleaning complete! Check netflix_titles_cleaned.csv for the cleaned dataset.")
    print("\nFinal dataset info:")
    print(df.info())
    print("\nFinal missing values:")
    print(df.isnull().sum())
    
    # Display sample of converted columns
    print("\nSample of converted columns:")
    print("\nDirectors sample:")
    print(df['director'].head())
    print("\nCast sample:")
    print(df['cast'].head())
    print("\nCountries sample:")
    print(df['country'].head())
    print("\nListed in sample:")
    print(df['listed_in'].head())
    
    # Display sample of duration values
    print("\nSample of duration values:")
    print("\nTV Shows duration sample:")
    print(df[df['type'] == 'TV Show']['duration'].head())
    print("\nMovies duration sample:")
    print(df[df['type'] == 'Movie']['duration'].head())

if __name__ == "__main__":
    clean_netflix_data() 