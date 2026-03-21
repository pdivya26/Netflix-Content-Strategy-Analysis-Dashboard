import streamlit as st
import pandas as pd
import plotly.express as px

# ---- 1. Page Config & Brand Styling ----
st.set_page_config(page_title="Netflix Analytics", layout="wide")

NETFLIX_RED = "#E50914"
px.defaults.template = "plotly_dark"
# Setting the default color for all bar/histogram charts to Red
px.defaults.color_discrete_sequence = [NETFLIX_RED]

# Custom CSS for Netflix Red Theme and Tab Fonts
st.markdown(f"""
    <style>
    /* Metric Card Styling */
    .stMetric {{ 
        background-color: #1a1a1a; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid {NETFLIX_RED}; 
    }}

    /* Force Sharp Edges */
    [data-testid="stSidebar"] img {{
        border-radius: 0px !important;
        border: none !important;
        /* Ensure no "soft" edges from shadows or padding */
        box-shadow: none !important;
    }}
    
    /* Tab Labels Font and Size */
    div[data-baseweb="tab-list"] button {{
        font-size: 26px !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
    }}

    /* Active Tab Red Highlight */
    div[data-baseweb="tab-list"] button[aria-selected="true"] {{
        color: {NETFLIX_RED} !important;
        margin-bottom: 10px;
    }}

    /* Font colors of insights */
    .stAlert {{
        border-radius: 0px !important;
    }}

    .stAlert p, .stAlert div {{
        color: #FFFFFF !important; /* Force text to White */
        font-size: 16px !important;
        font-weight: 500 !important;
    }}

    footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv("Netflix_Cleaned_Dataset.csv")
    df['year_added'] = pd.to_numeric(df['year_added'], errors='coerce')
    df['duration_num'] = pd.to_numeric(df['duration_num'], errors='coerce')
    return df

df = load_data()

# ---- 2. Sidebar with Logo & Search ----
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg", width=150)
st.sidebar.header("Filters and Search")

search_query = st.sidebar.text_input("Search Titles", "")

type_filter = st.sidebar.multiselect(
    "Type",
    options=sorted(df['type'].dropna().unique()),
    default=sorted(df['type'].dropna().unique())
)

year_min = int(df['year_added'].dropna().min())
year_max = int(df['year_added'].dropna().max())
year_filter = st.sidebar.slider("Year Added", year_min, year_max, (year_min, year_max))

# ---- 3. Filtering Logic ----
filtered_df = df[
    (df['type'].isin(type_filter)) &
    ((df['year_added'].between(year_filter[0], year_filter[1])) | (df['year_added'].isna()))
]

if search_query:
    filtered_df = filtered_df[filtered_df['title'].str.contains(search_query, case=False, na=False)]

# ---- 4. Dynamic Insight Calculations ----
def get_dynamic_insights(data):
    if data.empty:
        return "No data.", "No data.", "No data.", "No data.", "No data."
    
    m_pct = (data['type'] == 'Movie').mean() * 100
    t_pct = (data['type'] == 'TV Show').mean() * 100
    ins_mix = f"Movies dominate with {m_pct:.1f}% of the catalog, while TV Shows account for {t_pct:.1f}%."
    
    trend = data[data['year_added'].notna()].groupby('year_added').size().sort_index()
    if not trend.empty:
        peak_year = trend.idxmax()
        peak_value = trend.max()
        
        ins_growth = f"Content additions peaked in {int(peak_year)} with {peak_value} titles."
    else:
        ins_growth = "Growth trend unavailable."
    
    ins_country = f"Lead Producer: {data[data['main_country']!='Unknown']['main_country'].mode()[0]}" if not data[data['main_country']!='Unknown'].empty else "N/A"
    ins_genre = f"Top Genre: {data['main_genre'].mode()[0]}" if not data['main_genre'].empty else "N/A"
    ins_rating = f"Most Common Rating: {data['rating'].mode()[0]}" if not data['rating'].empty else "N/A"
    
    return ins_mix, ins_growth, ins_country, ins_genre, ins_rating

ins_mix, ins_growth, ins_country, ins_genre, ins_rating = get_dynamic_insights(filtered_df)

# ---- 5. Layout & Tabs ----
st.markdown(
    f"""
    <h1 style='text-align: center;'>
        Netflix Content Strategy Dashboard
    </h1>
    """, 
    unsafe_allow_html=True
)

tab_viz, tab_explore = st.tabs(["Analytics", "Data Explorer"])

with tab_viz:
    # Row 0: KPIs
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Titles", f"{len(filtered_df):,}")
    k2.metric("Movies", (filtered_df['type'] == 'Movie').sum())
    k3.metric("TV Shows", (filtered_df['type'] == 'TV Show').sum())
    k4.metric("Total Countries", filtered_df[filtered_df['main_country'] != 'Unknown']['main_country'].nunique())
    k5.metric("Total Genres", filtered_df['main_genre'].nunique())

    st.markdown("---")

    # Row 1: Mix and Trend
    colA, colB = st.columns(2)
    with colA:
        fig_type = px.bar(filtered_df['type'].value_counts().reset_index(), x='type', y='count', title='Content Distribution by Type',
        labels={'type': 'Content Type', 'count': 'No. of Titles'})
        fig_type.update_traces(marker_color=NETFLIX_RED)
        st.plotly_chart(fig_type, use_container_width=True)
        st.info(f"{ins_mix}")

    with colB:
        trend_combined = filtered_df[filtered_df['year_added'].notna()].groupby(['year_added', 'type']).size().reset_index(name='Count')
        fig_trend = px.line(
            trend_combined, 
            x='year_added', 
            y='Count', 
            color='type', 
            title='Content Growth Over Time: Movies vs TV Shows', 
            labels={'year_added': 'Year Added', 'Count': 'Number of Titles'},
            markers=True, 
            color_discrete_map={'Movie': NETFLIX_RED, 'TV Show': '#ff4b4b'}
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        st.info(f"{ins_growth}")
        
    # Find peak year
    trend = filtered_df[filtered_df['year_added'].notna()].groupby('year_added').size()

    if not trend.empty:
        peak_year = int(trend.idxmax())

        # Find dominant type in peak year
        peak_data = filtered_df[filtered_df['year_added'] == peak_year]
        dominant_type = peak_data['type'].mode()[0]

        movie_count = (peak_data['type'] == 'Movie').sum()
        tv_count = (peak_data['type'] == 'TV Show').sum()

        st.markdown("<br>", unsafe_allow_html=True)
        
        st.success(
            f"In {peak_year}, Netflix added {movie_count} Movies and {tv_count} TV Shows, highlighting Netflix’s peak global content expansion."
        )

    # Row 2: Countries and Genres
    colC, colD = st.columns(2)
    with colC:
        country_df = filtered_df[filtered_df['main_country'] != 'Unknown']['main_country'].value_counts().head(10).reset_index()
        fig_country = px.bar(country_df, x='count', y='main_country', orientation='h', title='Top 10 Producing Countries',
        labels={'count': 'Number of Titles', 'main_country': 'Country'})
        fig_country.update_traces(marker_color=NETFLIX_RED)
        st.plotly_chart(fig_country, use_container_width=True)
        st.info(f"{ins_country}")

    with colD:
        genre_df = filtered_df['main_genre'].value_counts().head(10).reset_index()
        fig_genre = px.bar(genre_df, x='main_genre', y='count', title='Top 10 Genres',
        labels={'main_genre': 'Genre', 'count': 'Number of Titles'})
        fig_genre.update_traces(marker_color=NETFLIX_RED)
        st.plotly_chart(fig_genre, use_container_width=True)
        st.info(f"{ins_genre}")

    st.markdown("---")
    # Row 3: Ratings
    fig_rating = px.bar(filtered_df['rating'].value_counts().reset_index(), x='rating', y='count', title='Ratings Distribution',
    labels={'rating': 'Rating', 'count': 'Number of Titles'})
    fig_rating.update_traces(marker_color=NETFLIX_RED)
    st.plotly_chart(fig_rating, use_container_width=True)
    st.info(f"{ins_rating}")

    # Row 4: Duration Analysis
    st.subheader("Content Duration Insights")
    col_dur1, col_dur2 = st.columns(2)
    
    with col_dur1:
        movie_df = filtered_df[filtered_df['type'] == 'Movie']
        fig_movie_dur = px.histogram(movie_df, x='duration_num', nbins=30, title="Movie Runtime (Minutes)", color_discrete_sequence=[NETFLIX_RED],
        labels={'duration_num': 'Runtime (Minutes)'})
        fig_movie_dur.update_layout(yaxis_title="Number of Titles")
        st.plotly_chart(fig_movie_dur, use_container_width=True)
        if not movie_df.empty:
            st.info(f"Peak runtime is {int(movie_df['duration_num'].mode()[0])} min.")

    with col_dur2:
        tv_df = filtered_df[filtered_df['type'] == 'TV Show']
        fig_tv_dur = px.histogram(
            tv_df,
            x='duration_num',
            nbins=10,
            title="TV Show Seasons Distribution",
            color_discrete_sequence=[NETFLIX_RED],
            labels={'duration_num': 'Number of Seasons'}
        )
        fig_tv_dur.update_layout(yaxis_title="Number of Titles")
        st.plotly_chart(fig_tv_dur, use_container_width=True)
        if not tv_df.empty:
            st.info(f"Most TV shows run for {int(tv_df['duration_num'].mode()[0])} season(s).")

# ---- 6. Data Explorer Tab ----
with tab_explore:
    st.subheader("Explore Filtered Catalog")
    st.dataframe(filtered_df, use_container_width=True)
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Download CSV", data=csv, file_name='netflix_data.csv', mime='text/csv')
