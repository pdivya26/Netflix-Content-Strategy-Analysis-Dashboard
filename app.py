import streamlit as st
import pandas as pd
import plotly.express as px

# ---- 1. Page Config & Brand Styling ----
st.set_page_config(page_title="Netflix Content Strategy Analysis Dashboard", layout="wide")

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
        margin-top: 10px;
    }}
    
    /* Force Sharp Edges */
    [data-testid="stSidebar"] img {{ 
        border-radius: 0px !important;
        border: none !important;
        /* Ensure no "soft" edges from shadows or padding */
        box-shadow: none !important;
    }}
    
    /* Target the Tab Labels Font and Size */
    div[data-baseweb="tab-list"] button[data-baseweb="tab"] div {{
        font-size: 18px !important;
        font-weight: 700 !important;
        padding: 14px 28px !important;
        margin-right: 10px !important;
        margin-bottom: 15px !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
    }}

    /* Active Tab Red Highlight */
    div[data-baseweb="tab-list"] button[aria-selected="true"] p {{
        color: {NETFLIX_RED} !important;
        margin-bottom: 10px;
        font-weight: bold;
    }}

    /* Font colors of insights */
    .stAlert {{
        border-radius: 0px !important;
    }}

    .stAlert p, .stAlert div {{
        color: #FFFFFF 
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

# ---- 4. Dynamic Insight Calculations ----
def get_dynamic_insights(data):
    if data.empty:
        return "No data.", "No data.", "No data.", "No data.", "No data."
    
    m_pct = (data['type'] == 'Movie').mean() * 100
    t_pct = (data['type'] == 'TV Show').mean() * 100

    if abs(m_pct - t_pct) < 2:
        ins_mix = f"Movies and TV Shows are almost equally represented (~{m_pct:.1f}% vs {t_pct:.1f}%)."
    elif m_pct > t_pct:
        ins_mix = f"Movies dominate the catalog with {m_pct:.1f}%, compared to {t_pct:.1f}% TV Shows."
    else:
        ins_mix = f"TV Shows dominate the catalog with {t_pct:.1f}%, compared to {m_pct:.1f}% Movies."
    
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
        Netflix Content Strategy Analysis Dashboard
    </h1>
    """, 
    unsafe_allow_html=True
)
st.markdown("<br><br>", unsafe_allow_html=True)

tab_viz, tab_explore = st.tabs(["Analytics", "Data Explorer"])

with tab_viz:
    # Row 0: KPIs
    # --- KPI Calculations ---
    total_titles = len(filtered_df)

    avg_titles = 0
    df_f = filtered_df.copy()

    # clean data (match Power BI behavior)
    df_f = df_f[df_f['year_added'].notna()]
    df_f['year_added'] = df_f['year_added'].astype(int)

    # optional (ONLY if Power BI excludes 2024)
    df_f = df_f[df_f['year_added'] < 2024]

    # TOTAL TITLES (match COUNT in Power BI)
    total_titles_clean = df_f['show_id'].count()

    # ACTIVE YEARS (match DISTINCTCOUNT in Power BI)
    active_years = df_f['year_added'].nunique()

    # FINAL AVG
    avg_titles = round(total_titles_clean / active_years)

    top_rating = "N/A"
    if not filtered_df['rating'].dropna().empty:
        top_rating = filtered_df['rating'].mode()[0]

    # --- KPI Display ---
    k1, k2, k3 = st.columns(3)

    k1.metric("Total Titles", f"{total_titles:,}")
    k2.metric("Average Titles Added Per Year", avg_titles)
    k3.metric("Top Rating", top_rating)

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
            color_discrete_map={'Movie': NETFLIX_RED, 'TV Show': '#ff4b4b'}
        )

        # Add shading under lines
        fig_trend.update_traces(
            fill='tozeroy',
            mode='lines',
            line=dict(width=2)
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
        country_df = (
            filtered_df[filtered_df['main_country'] != 'Unknown']['main_country']
            .value_counts()
            .reset_index()
        )
        country_df.columns = ['main_country', 'count']
        country_df = country_df.sort_values(by='count', ascending=False).head(10)
        fig_country = px.bar(country_df, x='main_country', y='count', title='Top 10 Producing Countries',
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

    # ---- Month-wise Content Addition ----
    # Prepare monthly data
    month_df = (
        filtered_df.dropna(subset=['month_added'])
        .groupby('month_added')
        .size()
        .reset_index(name='count')
        .sort_values('month_added')
    )

    # Month labels
    month_map = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }

    month_df['month_name'] = month_df['month_added'].map(month_map)

    # Line + shading chart
    fig_month = px.line(
        month_df,
        x='month_name',
        y='count',
        markers=True,
        title='Netflix Content Seasonality (Monthly Trend)',
        labels={'month_name': 'Month', 'count': 'Number of Titles'}
    )
    
    fig_month.update_traces(
        fill='tozeroy',
        line=dict(color=NETFLIX_RED, width=3),
        marker=dict(size=6)
    )

    st.plotly_chart(fig_month, use_container_width=True)

    # ---- Dynamic Insight for Monthly Trend ----
    if not month_df.empty:
        peak_month_row = month_df.loc[month_df['count'].idxmax()]
        low_month_row = month_df.loc[month_df['count'].idxmin()]

        peak_month = peak_month_row['month_name']
        peak_count = peak_month_row['count']

        low_month = low_month_row['month_name']
        low_count = low_month_row['count']

        st.info(
            f"Netflix adds the highest amount of content in {peak_month} "
            f"({peak_count} titles), while {low_month} sees the lowest additions "
            f"({low_count} titles), revealing strong seasonal release patterns."
        )

# ---- 6. Data Explorer Tab ----
with tab_explore:
    st.subheader("Explore Filtered Catalog")

    # Search inside explorer only
    search_query = st.text_input("Search Titles")

    temp_df = filtered_df.copy()

    if search_query:
        temp_df = temp_df[temp_df['title'].str.contains(search_query, case=False, na=False)]

    st.dataframe(temp_df, use_container_width=True)

    csv = temp_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name='netflix_data.csv',
        mime='text/csv'
    )
