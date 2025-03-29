def main():
    st.set_page_config(
        page_title="Home - Netflix Graph Analysis",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for dark theme compatibility
    st.markdown("""
        <style>
        .stMetric {
            background-color: #262730;
            padding: 15px;
            border-radius: 10px;
        }
        .stMetric:hover {
            background-color: #2E3138;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🏠 Home")

    # ... existing code ... 

    # Create pie chart for node distribution
    fig = px.pie(
        counts_df,
        values='count',
        names='type',
        title='Node Types Distribution',
        color_discrete_sequence=px.colors.qualitative.Set3  # Using a color scheme that works well in dark mode
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#FAFAFA'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Display relationship counts
    rel_counts_query = """
    MATCH ()-[r]->()
    RETURN type(r) as type, count(r) as count
    ORDER BY count DESC
    """
    rel_counts = neo4j.query(rel_counts_query)
    rel_counts_df = pd.DataFrame(rel_counts)
    
    # Create donut chart for relationship distribution
    fig = px.pie(
        rel_counts_df,
        values='count',
        names='type',
        title='Relationship Types Distribution',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2  # Using a different color scheme for variety
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#FAFAFA'
    )
    st.plotly_chart(fig, use_container_width=True)

    # ... existing code ... 