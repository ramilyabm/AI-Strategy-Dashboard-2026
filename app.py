import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np # Needed for the 'Jitter' math

# 1. PAGE SETUP
st.set_page_config(page_title="AI Transformation: 10-Year Review", layout="wide")

st.markdown("""
    <div style="display: flex; justify-content: flex-end; padding: 10px;">
        <a href="https://www.linkedin.com/in/ramilyabakiyeva/" target="_blank" style="text-decoration: none; color: #0077B5; font-weight: 700; font-size: 0.9rem; border: 1px solid #0077B5; padding: 5px 15px; border-radius: 20px;">
            LinkedIn Profile
        </a>
    </div>
""", unsafe_allow_html=True)

# --- GRADIENT BACKGROUND ---
page_bg_img = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(to bottom, #ffffff 0%, #f7f9fc 100%);
}
[data-testid="stSidebar"] {
    background: #f8f9fa; /* Very light gray to separate it slightly */
}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)


# 2. LOAD & CLEAN DATA
@st.cache_data
def load_and_clean_all():
    macro = pd.read_csv('Data_project2 - macro.csv')
    roi = pd.read_csv('Data_project2 - roi.csv')
    sector = pd.read_csv('Data_project2 - sector.csv')
    parameters = pd.read_csv('Data_project2 - parameters.csv')
    usecase = pd.read_csv('Data_project2 - usecase.csv')
    objections = pd.read_csv('Data_project2 - objections.csv')
    internet = pd.read_csv('Data_project2 - internet.csv')

    # --- DATA CLEANING HELPER ---
    def clean_numeric(df, columns):
        for col in columns:
            if col in df.columns:
                # Remove $ and % and commas
                df[col] = df[col].astype(str).str.replace(r'[\$,%]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    # Apply standard cleaning
    macro = clean_numeric(macro, ['Total AI Spending ($B)', 'Enterprise Adoption', 'High-Performer EBIT Impact (%)'])
    roi = clean_numeric(roi, ['Impact_Score'])
    sector = clean_numeric(sector, ['Median ROI'])

    for df in [macro, roi, sector, parameters]:
        df.columns = df.columns.str.strip()

    # --- CLEAN PARAMETERS (The Fix) ---
    if 'Numeric' in parameters.columns:
        # 1. Regex Match: Keep ONLY digits and dots (removes 'B', 'M', ',', '$', spaces)
        parameters['Numeric'] = parameters['Numeric'].astype(str).str.replace(r'[^\d.]', '', regex=True)
        
        # 2. Convert to Number
        parameters['Numeric'] = pd.to_numeric(parameters['Numeric'], errors='coerce')
        
        # 3. CRITICAL: Drop rows where conversion failed (NaN) so Plotly doesn't crash
        parameters = parameters.dropna(subset=['Numeric'])

    # D. Clean Objections/Use Cases (Standardize Headers if needed)
    # We strip whitespace from headers just in case (" Industry " -> "Industry")
    usecase.columns = usecase.columns.str.strip()
    objections.columns = objections.columns.str.strip()

    # Standardizing Sector Names
    roi['Sector'] = roi['Sector'].replace({'Chips': 'Tech/SaaS', 'SaaS': 'Tech/SaaS', 'Health': 'Healthcare', 'Auto': 'Automotive', 'Consumer': 'Retail'})
    
    return macro, roi, sector, parameters, usecase, objections, internet

# --- LOAD DATA FIRST ---
df_macro, df_roi, df_sector, df_parameters, df_usecase, df_objections, df_internet = load_and_clean_all()

# --- TOP NAVIGATION & FILTERS ---

st.markdown("""
    <style>
    /* GLOBAL THEME OVERRIDE */
    :root {
        --st-accent-color: transparent !important;
        --st-primary-color: #1E3A8A !important;
    }

    /* HIDE EVERY POPUP VALUE */
    [data-baseweb="popover"], [data-baseweb="tooltip"], div[data-testid="stThumbValue"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        background-color: transparent !important;
        color: transparent !important;
    }
    /* 1. BRANDING & TEXT */
    .author-text {
        text-align: center; color: #64748B; font-size: 0.85rem;
        text-transform: uppercase; letter-spacing: 0.15em;
        margin-bottom: 5px; font-family: 'Helvetica Neue', sans-serif;
    }
    .title-text { 
        font-family: 'Helvetica Neue', sans-serif; font-weight: 800; 
        color: #1E3A8A; text-align: center; font-size: 3rem; 
        margin-top: 0px; margin-bottom: 5px; 
    }
    .subtitle-text { 
        font-family: 'Arial', sans-serif; color: #475569; 
        text-align: center; font-size: 1.1rem; margin-bottom: 30px; 
    }

    /* 2. THE TIMELINE RULER (Track with markers for each year) */
    div.stSlider > div[data-baseweb="slider"] > div > div {
        /* Creating vertical ticks: 11 years (2016-2026) = 10 intervals of 10% */
        background-image: linear-gradient(to right, #CBD5E1 2px, transparent 2px) !important;
        background-size: 10% 100% !important; 
        background-color: #F1F5F9 !important; 
        height: 12px !important;
        border-radius: 6px !important;
        border: 1px solid #E2E8F0 !important;
    }
    
    /* 3. THE ACTIVE SELECTION (The Blue Progress bar) */
    div.stSlider > div[data-baseweb="slider"] > div > div > div > div {
        background-color: #1E3A8A !important; 
    }

    /* 4. THE HANDLES (Clean White Circles with Blue Borders) */
    div.stSlider [role="slider"] {
        background-color: #FFFFFF !important;
        border: 3px solid #1E3A8A !important;
        box-shadow: 0 3px 6px rgba(0,0,0,0.15) !important;
        height: 24px !important;
        width: 24px !important;
        z-index: 10 !important;
    }
    
    /* Remove focus rings (the blue/red halos on click) */
    div.stSlider [role="slider"]:focus {
        outline: none !important;
        box-shadow: 0 0 0 6px rgba(30, 58, 138, 0.2) !important;
    }

    /* 5. THE "INVISIBLE" BUBBLE (Nuclear Fix for Red Text/Blue Shape) */
    /* Instead of 'display: none', we make everything transparent.
       This ensures the handle remains "grabbable". */
    div[data-testid="stThumbValue"], 
    div[data-testid="stThumbValue"] > div,
    div.stSlider div[data-baseweb="tooltip"] {
        background-color: transparent !important;
        color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        font-size: 0px !important;
        line-height: 0 !important;
    }

    /* 6. HIDE DEFAULT TICKS (The numbers at the bottom) */
    div[data-testid="stSliderTickBar"] { display: none !important; }
    </style>
    
    <div class="author-text">Prepared by Ramilya Bakiyeva — Tech Strategy & Analytics</div>
    <h1 class="title-text">AI Transformation: 10-Year Review</h1>
    <p class="subtitle-text">Interactive Strategic Analysis: From <b>Experimental AI</b> to <b>Agentic Scale</b></p>
    """, unsafe_allow_html=True)

# --- THE PLEASANT SLIDER (GLOBAL) ---
# We use a container to visually separate the filter from the tabs
# 4. HEADER & GLOBAL CONTROLLER (The Slider)
# =============================================================================
with st.container():
    min_year = int(df_macro['Year'].min())
    max_year = int(df_macro['Year'].max())
    
    # Clean Layout: Spacer | Slider | Spacer
    col_spacer_L, col_slider, col_spacer_R = st.columns([1, 6, 1])
    
    with col_slider:
        selected_range = st.slider(
            "Select Strategic Timeline:",
            min_year, max_year, (min_year, max_year),
            step=1,
            label_visibility="collapsed" 
        )

        # Big Bold Text Below to confirm selection
        st.markdown(f"""
        <div style='text-align: center; color: #1E3A8A; font-size: 1.2rem; font-weight: bold; margin-top: 5px;'>
            ⏱️ Period: {selected_range[0]} — {selected_range[1]}
        </div>
        """, unsafe_allow_html=True)

# --- GLOBAL FILTER LOGIC ---
current_years = list(range(selected_range[0], selected_range[1] + 1))

if not current_years:
    st.error("⚠️ Please select at least one year.")
    st.stop()

# --- GLOBAL DATA FILTER ---
# This variable 'current_years' will now be used by ALL tabs
current_years = list(range(selected_range[0], selected_range[1] + 1))

# --- CUSTOM CSS FOR BUTTON-STYLE TABS ---
st.markdown("""
<style>
    /* 1. MAKE TABS FULL WIDTH */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        width: 100%;
    }

    /* 2. TAB BUTTONS */
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F1F5F9;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #64748B;
        flex-grow: 1;
        text-align: center;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #E2E8F0;
        color: #1E3A8A;
    }

    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF;
        border-top: 3px solid #1E3A8A;
        color: #1E3A8A;
        font-weight: bold;
    }

    /* 3. METRIC VALUE (THE NUMBERS/TEXT) - ADAPTIVE SIZE */
    [data-testid="stMetricValue"] {
        font-size: 1.15rem !important; /* Smaller to fit "Multi-Agent..." */
        font-weight: 700 !important;  /* Bold */
        color: #1E3A8A;               /* Dark Blue */
        display: flex;
        justify-content: center;      /* Center the text/number */
        align-items: center;
        text-align: center;
        word-wrap: break-word;        /* Wrap if really long */
    }

    /* 4. METRIC LABEL (THE HEADERS) - BIGGER & CENTERED */
    [data-testid="stMetricLabel"] {
        font-size: 1.1rem !important; /* Increased from default */
        font-weight: 600;             /* Semi-bold */
        color: #475569;               /* Slate Gray */
        display: flex;
        justify-content: center;      /* Center the header */
        width: 100%;
    }

    /* 5. METRIC DELTA (The small +% number) */
    [data-testid="stMetricDelta"] {
        justify-content: center;      /* Center the small green/red arrow */
        font-weight: bold;
    }

    /* 6. LIGHT BLUE METRIC CARDS */
    [data-testid="stMetric"] {
        background-color: #EFF6FF; 
        border: 1px solid #DBEAFE; 
        padding: 15px;             
        border-radius: 12px;       
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        min-height: 110px;         /* Uniform height */
    }
</style>
""", unsafe_allow_html=True)


# --- CONNECTED METRICS (Top Row) ---
# Logic: We display the metrics for the LATEST year selected in the filter
if current_years:
    target_year = max(current_years)
else:
    target_year = 2026 # Fallback if list is somehow empty

# Get the data row for that specific year
metric_row = df_macro[df_macro['Year'] == target_year].iloc[0]

col1, col2, col3 = st.columns(3)

with col1:
    spend = metric_row['Total AI Spending ($B)']
    st.metric(
        label=f"Global AI Spend ({target_year})", 
        value=f"${spend}B", 
        delta="Annual Investment"
    )

with col2:
    # Converting decimal to percentage
    adopt = int(metric_row['Enterprise Adoption'] * 100)
    st.metric(
        label=f"Enterprise Adoption ({target_year})", 
        value=f"{adopt}%",
        delta="Market Penetration"
    )

with col3:
    ebit = round(metric_row['High-Performer EBIT Impact (%)'] * 100, 1)
    st.metric(
        label=f"Peak EBIT Impact ({target_year})", 
        value=f"{ebit}%",
        delta="Efficiency Gain"
    )

st.markdown("---")

# --- VISUALIZATIONS (3-File Integration) ---

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Macro Trends", "Sector Maturity", "Company Proof Points", "Model Intelligence", "AI Velocity", "Sales Enablement"])

with tab1:
    st.subheader("The Efficiency Gap: Investment vs. Return")
    
    # 1. FILTER DATA
    filtered_macro = df_macro[df_macro['Year'].isin(current_years)].copy()
    
    if not filtered_macro.empty:
        # --- SECTION A: THE "HEADLINE" METRICS (The "So What?") ---
        # We calculate the growth between the first and last selected year
        start_row = filtered_macro.iloc[0]
        end_row = filtered_macro.iloc[-1]
        
        # Calculate Delta
        spend_growth = end_row['Total AI Spending ($B)'] - start_row['Total AI Spending ($B)']
        ebit_growth = (end_row['High-Performer EBIT Impact (%)'] - start_row['High-Performer EBIT Impact (%)']) * 100
        
        # Display as Metric Cards
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Global AI Spend Growth", f"+${spend_growth:.1f}B", delta_color="inverse") # Spending going up is "cost"
        col_m2.metric("EBIT Margin Expansion", f"+{ebit_growth:.1f}%", delta_color="normal")   # Profit going up is "good"
        col_m3.metric("Current Tech Era", end_row['AI Productivity Frontier'])
        
        st.markdown("---")

        # --- NEW SECTION B: THE NARRATIVE (MOVED HERE) ---
        latest_data = filtered_macro.iloc[-1]
        
        st.markdown(f"""
            <div style="background-color: #F0FDF4; border-left: 5px solid #16A34A; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
                <p style="color: #166534; font-weight: 800; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">
                    Strategic Insight: The Value Shift
                </p>
                <ul style="margin: 0; padding-left: 20px; color: #14532D; font-size: 1.05rem; line-height: 1.7;">
                    <li style="margin-bottom: 8px;">
                        <b>In {latest_data['Year']}:</b> The dominant tech is <b>{latest_data['AI Productivity Frontier']}</b>.
                    </li>
                    <li style="margin-bottom: 8px;">
                        <b>The Shift:</b> {latest_data['Breakthrough Explanation in Simple Terms']}
                    </li>
                    <li>
                        <b>Business Impact:</b> {latest_data.get('Reliable Tech Context', 'High ROI deployments.')}
                    </li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    
        # --- SECTION B: THE VISUAL STORY ---
        fig_macro = go.Figure()

        # Trace 1: Spend (The Cost) - Grey Bars
        fig_macro.add_trace(go.Bar(
            x=filtered_macro['Year'], 
            y=filtered_macro['Total AI Spending ($B)'], 
            name="Global Spend ($B)",
            marker_color='#CFD8DC', # Light Blue-Grey (Subtle)
            opacity=0.6,
            hovertemplate="<b>Year: %{x}</b><br>Spend: $%{y}B<extra></extra>"
        ))

        # Trace 2: EBIT Impact (The Value) - Green Line
        # We multiply by 100 to show as percentage points 
        # (Note: In CSV, 0.012 is 1.2%, so we multiply by 100)
        fig_macro.add_trace(go.Scatter(
            x=filtered_macro['Year'], 
            y=filtered_macro['High-Performer EBIT Impact (%)'] * 100, 
            name="EBIT Impact (%)",
            mode='lines+markers+text',
            text=[f"{val*100:.1f}%" for val in filtered_macro['High-Performer EBIT Impact (%)']], # Show % on the line
            textposition="top center",
            yaxis="y2",
            line=dict(color='#00C853', width=4), # Bright Green
            marker=dict(size=12, color='#1B5E20', line=dict(width=2, color='white'))
        ))

        # Annotations: The "Eras" of AI
        # We hardcode these zones to tell the story of "Why" it changed
        fig_macro.add_vrect(
            x0=2015.5, x1=2022.5, 
            fillcolor="#FFEBEE", opacity=0.5, layer="below", line_width=0,
            annotation_text="<b>Experimental Era</b><br>(High Cost, Low ROI)", annotation_position="top left"
        )
        
        fig_macro.add_vrect(
            x0=2022.5, x1=2026.5, 
            fillcolor="#E8F5E9", opacity=0.5, layer="below", line_width=0,
            annotation_text="<b>Value Era</b><br>(Agentic Scale)", annotation_position="top right"
        )

        # Layout Improvements
        fig_macro.update_layout(
            title="The divergence: Value (Green) is finally outpacing Cost (Grey)",
            xaxis=dict(tickmode='array', tickvals=current_years),
            yaxis=dict(title="Global Spend ($B)", showgrid=False),
            yaxis2=dict(overlaying="y", side="right", title="EBIT Margin Impact (%)", showgrid=False, ticksuffix="%"),
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
            hovermode="x unified",
            height=500
        )
        
        st.plotly_chart(fig_macro, use_container_width=True)

    else:
        st.warning("No data available for the selected timeline.")


with tab2:
    st.subheader("Sector Maturity: From Prediction to Autonomy")
    
    # 1. DATA PREP & CLEANING
    df_sector_clean = df_sector.copy()
    df_sector_clean.columns = df_sector_clean.columns.str.strip()
    
    # Force Numeric: Handle both 0.35 and 35.0 formats
    df_sector_clean['Median ROI'] = pd.to_numeric(df_sector_clean['Median ROI'], errors='coerce')
    
    # Standardization: Ensure we are working with 0-100 scale for visual logic
    if df_sector_clean['Median ROI'].max() <= 1.0:
        df_sector_clean['ROI_Val'] = df_sector_clean['Median ROI'] * 100
    else:
        df_sector_clean['ROI_Val'] = df_sector_clean['Median ROI']

    avg_roi = df_sector_clean['ROI_Val'].mean()
    best_sector = df_sector_clean.loc[df_sector_clean['ROI_Val'].idxmax()]

    # --- SECTION A: STRATEGIC INSIGHT BOX ---
    st.markdown(f"""
        <div style="background-color: #F0FDF4; border-left: 5px solid #16A34A; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
            <p style="color: #166534; font-weight: 800; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">
                Strategic Insight: The Autonomy Premium
            </p>
            <ul style="margin: 0; padding-left: 20px; color: #14532D; font-size: 1.05rem; line-height: 1.7;">
                <li style="margin-bottom: 8px;">
                    <b>Performance Leader:</b> The <b>{best_sector['Industry']}</b> sector is outperforming the market with a <b>{best_sector['ROI_Val']:.0f}% ROI</b>.
                </li>
                <li style="margin-bottom: 8px;">
                    <b>Market Benchmark:</b> The average cross-sector ROI stands at <b>{avg_roi:.0f}%</b>, creating a clear gap between leaders and laggards.
                </li>
                <li>
                    <b>The "So What":</b> The value shift is driven by <b>Autonomy</b>—moving from AI that identifies problems to Agentic workflows that fix them.
                </li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns([1.5, 2.5]) # Give the table more width for the new columns
    
    with col_a:
        st.markdown("##### ROI Performance by Industry")
        
        fig_sector = px.bar(
            df_sector_clean.sort_values('ROI_Val'), 
            x='ROI_Val', y='Industry', orientation='h',
            color='ROI_Val', 
            color_continuous_scale='Teal',
            height=480,
            custom_data=['Industry', 'ROI_Val', 'Agentic AI (2024-26)']
        )
        
        # Red Reference Line for Average
        fig_sector.add_vline(x=avg_roi, line_width=2, line_dash="dash", line_color="#DC2626", 
                             annotation_text="Avg", annotation_position="bottom right")

        fig_sector.update_traces(
            texttemplate='%{x:.1f}%', textposition='outside',
            hovertemplate="<b>%{customdata[0]}</b><br>ROI: %{customdata[1]:.1f}%<br>Next: %{customdata[2]}<extra></extra>",
            hoverlabel=dict(bgcolor="white", font_size=13, bordercolor="#1E3A8A")
        )

        fig_sector.update_layout(
            xaxis_title="Median ROI (%)", yaxis_title=None,
            coloraxis_showscale=False, margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(range=[0, df_sector_clean['ROI_Val'].max() + 10])
        )
        st.plotly_chart(fig_sector, use_container_width=True)

    with col_b:
        # --- 1. PRECISION ALIGNED HEADERS ---
        # We increase the 'width' of the first two items to push Legacy to the right
        # We use 'border-left' as visual guides to match the dataframe lines
        st.markdown("""
            <div style="display: flex; background-color: #0F172A; padding: 12px 0px; border-radius: 8px 8px 0 0; border-bottom: 2px solid #334155; width: 100%;">
                <div style="width: 20%; color: #FFFFFF; font-weight: 700; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; padding-left: 15px;">Sector</div>
                <div style="width: 15%; color: #FFFFFF; font-weight: 700; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Maturity</div>
                <div style="width: 25%; color: #94A3B8; font-weight: 700; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; padding-left: 7px;">Legacy Era</div>
                <div style="width: 30%; color: #38BDF8; font-weight: 800; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; padding-left: 7px;">Agentic Frontier</div>
                <div style="width: 10%; color: #FFFFFF; font-weight: 700; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; padding-left: 5px;">Trend</div>
            </div>
        """, unsafe_allow_html=True)

        # --- 2. DATA PREP & HEIGHT FIX ---
        df_display = df_sector_clean.sort_values('ROI_Val', ascending=False).reset_index(drop=True)
        
        # FIXED HEIGHT: 35px per row + 40px for header. 
        # This removes all "extra rows" at the bottom.
        row_height = 35 
        header_height = 40
        dynamic_height = (len(df_display) * row_height) + header_height + 5

        st.dataframe(
            df_display[['Industry', 'ROI_Val', 'Legacy AI (2016-21)', 'Agentic AI (2024-26)', 'Trend']],
            column_config={
                "Industry": st.column_config.TextColumn(None, width="small"),
                "ROI_Val": st.column_config.ProgressColumn(
                    None,
                    format="%d%%",
                    min_value=0,
                    max_value=50,
                    width="small"
                ),
                "Legacy AI (2016-21)": st.column_config.TextColumn(None, width="medium"),
                "Agentic AI (2024-26)": st.column_config.TextColumn(None, width="medium"),
                "Trend": st.column_config.TextColumn(None, width="small"),
            },
            hide_index=True,
            use_container_width=True,
            height=dynamic_height 
        )


with tab3:
    st.subheader("The AI Value Wave: From Prediction to Agency")

    # 1. GLOBAL FILTER
    filtered_roi = df_roi[df_roi['Year'].isin(current_years)].copy()

    if not filtered_roi.empty:
        # --- JITTER ---
        noise = np.random.uniform(-0.15, 0.15, size=len(filtered_roi))
        filtered_roi['Year_Jitter'] = filtered_roi['Year'] + noise

        # 2. COLOR PALETTES (Dark for Dot, Light for Tooltip)
        category_colors = {
            'Infrastructure': '#636EFA',  # Deep Blue
            'Predictive': '#AB63FA',      # Deep Purple
            'Agentic': '#00CC96'          # Deep Green
        }
        
        # Pastel versions for the tooltip background
        tooltip_colors = {
            'Infrastructure': '#E8EAF6',  # Very Light Indigo
            'Predictive': '#F3E5F5',      # Very Light Purple
            'Agentic': '#E0F2F1'          # Very Light Teal
        }

        # 3. BUILD CHART
        fig_bubble = px.scatter(
            filtered_roi, 
            x="Year_Jitter", 
            y="Impact_Score", 
            size="Impact_Score", 
            color="AI Category", 
            color_discrete_map=category_colors,
            # CRITICAL: We pass all the text fields we need for the fancy tooltip here
            # custom_data order: [0]=Company, [1]=Sector, [2]=Value, [3]=Logic, [4]=Category
            custom_data=['Company', 'Sector', 'Quantitative Value', 'Score_Logic', 'AI Category'],
            title=f"Corporate Impact Scores (Showing {len(filtered_roi)} Companies)",
        )

        # 4. THE "COMPELLING" TOOLTIP LOGIC
        # We iterate through each category trace to give it a specific background color
        for trace in fig_bubble.data:
            # trace.name is the Category (e.g., 'Agentic')
            if trace.name in tooltip_colors:
                # Set the background color of the box
                trace.hoverlabel.bgcolor = tooltip_colors[trace.name]
                # Set the border color to match the dot
                trace.hoverlabel.bordercolor = category_colors[trace.name]
                # Make sure the text is dark (since bg is light)
                trace.hoverlabel.font = dict(color='#1A237E', size=13, family="Arial")
                
                # HTML TEMPLATE for the "Compelling" look
                trace.hovertemplate = (
                    "<b>%{customdata[0]}</b> <span style='color:gray'>(%{customdata[1]})</span><br>" # Header: Company (Sector)
                    "--------------------------------------------------<br>"
                    "<b>Value:</b> %{customdata[2]}<br>" # The "Hero" Metric
                    "<i>%{customdata[3]}</i><br>" # The Logic
                    "<extra></extra>" # Hides the messy 'trace name' on the side
                )

        # Final Layout Polish
        fig_bubble.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey'), opacity=0.9))
        fig_bubble.update_layout(
            xaxis=dict(title="Year", tickmode='linear', tickvals=current_years),
            yaxis=dict(title="Impact Score (1-10)", range=[0, 11]),
            legend_title_text="Tech Category",
            hovermode="closest" # Ensures popup appears exactly on the bubble
        )
        
        st.plotly_chart(fig_bubble, use_container_width=True)

        st.markdown("---")

        st.markdown("##### 2. Detailed Evidence: The Proof in the P&L")
    
        # 1. DATA PREP & HEIGHT CALCULATION
        # Clean the data and ensure columns exist
        df_evidence = filtered_roi[['Company', 'Sector', 'Quantitative Value', 'AI Category', 'Impact_Score', 'Score_Logic']].copy()
        df_evidence.columns = df_evidence.columns.str.strip()

        # Dynamic Height Calculation (Strict: 35px per row + 45px padding)
        # This snaps the table to the bottom of the last row
        row_count = len(df_evidence)
        dynamic_height = (row_count * 35) + 45 if row_count > 0 else 100

        # --- 2. PRECISION ALIGNED HEADERS (NO EMOJIS) ---
        # Percentages tuned to match Streamlit's 'small', 'medium', 'large' internal widths
        st.markdown("""
            <div style="display: flex; background-color: #0F172A; padding: 12px 0px; border-radius: 8px 8px 0 0; border-bottom: 2px solid #334155; width: 100%;">
                <div style="width: 12%; color: #FFFFFF; font-weight: 700; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; padding-left: 15px;">Entity</div>
                <div style="width: 13%; color: #FFFFFF; font-weight: 700; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Sector</div>
                <div style="width: 20%; color: #34D399; font-weight: 800; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; border-left: 1px solid #334155; padding-left: 10px;">Financial Result</div>
                <div style="width: 12%; color: #38BDF8; font-weight: 800; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; border-left: 1px solid #334155; padding-left: 10px;">AI Category</div>
                <div style="width: 13%; color: #FBBF24; font-weight: 800; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; border-left: 1px solid #334155; padding-left: 10px;">Impact Score</div>
                <div style="width: 30%; color: #FFFFFF; font-weight: 700; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; border-left: 1px solid #334155; padding-left: 10px;">Strategic Logic</div>
            </div>
        """, unsafe_allow_html=True)

        # --- 3. THE BEAUTIFIED DATAFRAME ---
        st.dataframe(
            df_evidence,
            column_config={
                "Company": st.column_config.TextColumn(None, width="small"),
                "Sector": st.column_config.TextColumn(None, width="small"),
                "Quantitative Value": st.column_config.TextColumn(None, width="medium"),
                "AI Category": st.column_config.TextColumn(None, width="small"),
                "Impact_Score": st.column_config.ProgressColumn(
                    None, # Label hidden to use custom header
                    help="A scale of 1-10 based on P&L impact",
                    format="%d",
                    min_value=0,
                    max_value=10,
                    width="small"
                ),
                "Score_Logic": st.column_config.TextColumn(None, width="large"),
            },
            hide_index=True,
            use_container_width=True,
            height=dynamic_height
        )
        
    else:
        st.warning("No company data available for the selected years.")

with tab4:
    st.subheader("The Scale of Intelligence: Why Spend is Skyrocketing")

    # --- 1. DATA PREP ---
    df_parameters.columns = df_parameters.columns.str.strip()
    filtered_params = df_parameters[df_parameters['Year'].isin(current_years)].copy()
    
    # Cleaning for MMLU and Context
    filtered_params['MMLU_Clean'] = pd.to_numeric(filtered_params['MMLU Score'], errors='coerce')
    if filtered_params['MMLU_Clean'].max() <= 1.0:
        filtered_params['MMLU_Clean'] = filtered_params['MMLU_Clean'] * 100
        
    filtered_params['Context_Clean'] = pd.to_numeric(
        filtered_params['Context Window'].astype(str).str.replace(',', '').str.replace('N/A', '0'), 
        errors='coerce'
    )

    # --- SECTION A: THE PHYSICAL SCALE ---
    st.markdown("#### 1. The Physical Scale: Model Parameters")
    
    # 💡 IMPROVED INSIGHT BOX: Before the Chart
    st.markdown("""
        <div style="background-color: #F0F9FF; border-left: 5px solid #1E3A8A; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
            <p style="color: #1E3A8A; font-weight: 800; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;">
                Strategic Insight: The Scaling Law
            </p>
            <p style="color: #334155; font-size: 1.05rem; line-height: 1.6;">
                AI capability follows a predictable <b>Scaling Law</b>: for every 10x increase in compute and parameters, we see a linear jump in reasoning ability. 
                This chart tracks the transition from millions to <b>trillions</b> of connections, defining the "Physical" size of the AI brain.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # SCATTER PLOT
    fig_params = px.scatter(
        filtered_params.dropna(subset=['Numeric']),
        x="Year", y="Numeric", color="Developer",
        log_y=True, height=450,
        custom_data=['Model Name', 'Developer', 'Number of Parameters']
    )

    # FIX: Clean Tooltip (No <div> tags)
    fig_params.update_traces(
        marker=dict(size=16, line=dict(width=1.5, color='white'), opacity=0.85),
        hovertemplate="""
            <b>%{customdata[0]}</b><br>
            Developer: %{customdata[1]}<br>
            Total Size: %{customdata[2]}<br>
            <extra></extra>
        """,
        hoverlabel=dict(
            bgcolor="white", 
            font_size=14, 
            font_family="Inter, sans-serif",
            bordercolor="#1E3A8A" # This keeps the look premium
        )
    )

    fig_params.update_layout(yaxis_title="Parameters (Exponential Scale)", xaxis_title=None, hovermode="closest")
    st.plotly_chart(fig_params, use_container_width=True)

    st.markdown("---")

    # --- SECTION B: THE INTELLIGENCE FRONTIER ---
    st.markdown("#### 2. The Intelligence Frontier: IQ & Working Memory")

    # 💡 DIVIDED INSIGHT TABLES: Two Beautiful Boxes
    col_ins1, col_ins2 = st.columns(2)
    with col_ins1:
        st.markdown("""
            <div style="background-color: #F8FAFC; border-top: 5px solid #1E3A8A; padding: 18px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); height: 100%;">
                <h5 style="color: #1E3A8A; margin-top: 0;">REASONING (MMLU)</h5>
                <p style="color: #475569; font-size: 0.95rem;">
                    Measures general IQ across 57 subjects. The shift from <b>36%</b> (GPT-2) to <b>86%+</b> (GPT-4) signifies the transition from word prediction to human-level logic.
                </p>
            </div>
        """, unsafe_allow_html=True)
    with col_ins2:
        st.markdown("""
            <div style="background-color: #F8FAFC; border-top: 5px solid #DC2626; padding: 18px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); height: 100%;">
                <h5 style="color: #DC2626; margin-top: 0;">MEMORY (CONTEXT WINDOW)</h5>
                <p style="color: #475569; font-size: 0.95rem;">
                    The "Desk Space" of AI. 128k+ tokens allow the model to "read" and reason across thousands of pages of your data in a single prompt.
                </p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("####") # Spacer

    # DUAL-AXIS CHART
    fig_iq = go.Figure()

    # MMLU IQ (Bars)
    fig_iq.add_trace(go.Bar(
        x=filtered_params['Model Name'], 
        y=filtered_params['MMLU_Clean'],
        name="MMLU IQ Score",
        marker_color='#1E3A8A', opacity=0.75,
        customdata=filtered_params[['Number of Parameters', 'Developer']].values,
        hovertemplate="""
            <b>%{x}</b><br>
            IQ Score: %{y:.1f}%<br>
            Developer: %{customdata[1]}<br>
            Size: %{customdata[0]}<br>
            <extra></extra>"""
    ))

    # Context Window (Line)
    fig_iq.add_trace(go.Scatter(
        x=filtered_params['Model Name'], 
        y=filtered_params['Context_Clean'],
        name="Context Window (Memory)", 
        yaxis="y2", mode="lines+markers",
        line=dict(color='#DC2626', width=4),
        marker=dict(size=12, symbol="diamond", line=dict(width=2, color="white")),
        customdata=filtered_params[['Number of Parameters', 'Developer']].values,
        hovertemplate="""
            <b>%{x}</b><br>
            Memory: %{y:,.0f} tokens<br>
            Model Size: %{customdata[0]}<br>
            <extra></extra>"""
    ))

    fig_iq.update_layout(
        yaxis=dict(title="MMLU Score (%)", range=[0, 100], gridcolor='#F1F5F9'),
        yaxis2=dict(title="Context tokens (Log Scale)", overlaying="y", side="right", type="log"),
        legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
        height=550, margin=dict(l=0, r=0, t=20, b=0),
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="Arial")
    )
    st.plotly_chart(fig_iq, use_container_width=True)

with tab5:
    st.subheader("The Velocity Matrix: Benchmarking the AI Era")

    # --- 1. DATA PREP ---
    df_int = df_internet.copy()
    df_int.columns = df_int.columns.str.strip()
    
    def get_raw_val(metric_name, col_name):
        return df_int.loc[df_int['Metric'] == metric_name, col_name].values[0]

    def to_float(val):
        try:
            return float(str(val).replace(',', '').replace('$', '').replace('%', '').strip())
        except: return 0.0

    # --- 2. STRATEGIC COMPARATIVE NARRATIVE ---
    st.markdown(f"""
        <div style="background-color: #F8FAFC; border-left: 5px solid #0F172A; padding: 25px; border-radius: 8px; margin-bottom: 20px;">
            <p style="color: #0F172A; font-weight: 800; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 10px;">
                Strategic Comparative: Three Eras of Disruption
            </p>
            <p style="color: #334155; font-size: 1.1rem; line-height: 1.6; margin: 0;">
                We compare these eras to track the <b>Evolution of Leverage</b>: how humanity moved from building the physical rails of connectivity (Internet) to scaling utility (SaaS), and finally to the <b>Automation of Reasoning (AI)</b>.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --- 3. FOUNDATIONAL SHIFT RIBBON (REFINED) ---
    st.markdown(f"""
        <div style="background-color: #0F172A; padding: 20px; border-radius: 8px; margin-bottom: 30px; display: flex; justify-content: space-around; text-align: center;">
            <div style="flex: 1; border-right: 1px solid #334155;">
                <p style="color: #94A3B8; font-size: 0.7rem; text-transform: uppercase; margin-bottom: 5px;">Cycle Focus</p>
                <p style="color: #FFFFFF; font-size: 0.9rem; font-weight: 700;">{get_raw_val('Cycle Focus', 'Internet_Val')} → {get_raw_val('Cycle Focus', 'SaaS_Val')} → {get_raw_val('Cycle Focus', 'AI_Val')}</p>
            </div>
            <div style="flex: 1;">
                <p style="color: #94A3B8; font-size: 0.7rem; text-transform: uppercase; margin-bottom: 5px;">Infrastructure Base</p>
                <p style="color: #38BDF8; font-size: 0.9rem; font-weight: 700;">Fiber/Telecom → Public Cloud → GPU/Compute</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- 4. THE VISUAL BENCHMARK GRID (4 GRAPHS) ---
    metrics_to_graph = ['Time to 100M Users', 'Peak Infra Spend', 'Rev per Employee', 'Startup Entry Cost']
    
    col_left, col_right = st.columns(2)
    
    for i, m_name in enumerate(metrics_to_graph):
        target_col = col_left if i % 2 == 0 else col_right
        row = df_int[df_int['Metric'] == m_name].iloc[0]
        
        with target_col:
            # Data Prep with Year Mapping for Hover
            era_data = pd.DataFrame({
                'Era': ['Internet', 'SaaS', 'AI Era'],
                'Value': [to_float(row['Internet_Val']), to_float(row['SaaS_Val']), to_float(row['AI_Val'])],
                'Display': [row['Internet_Val'], row['SaaS_Val'], row['AI_Val']],
                'Year': [row['Internet_Year'], row['SaaS_Year'], row['AI_Year']]
            })
            
            fig = px.bar(
                era_data, x='Era', y='Value', text='Display',
                color='Era', color_discrete_map={'Internet': '#94A3B8', 'SaaS': '#1E3A8A', 'AI Era': '#38BDF8'},
                title=f"<b>{m_name} ({row['Unit']})</b>"
            )
            
            # HOVER TEXT: Pulls Era and Year dynamically
            fig.update_traces(
                textposition='outside',
                customdata=era_data['Year'],
                hovertemplate="<b>%{x} Era</b><br>Benchmark Year: %{customdata}<br>Value: %{text}<extra></extra>"
            )
            
            fig.update_layout(showlegend=False, height=320, margin=dict(l=10, r=10, t=50, b=10), yaxis_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # --- DYNAMIC SUMMARY TEXT BOXES ---
            if m_name == 'Time to 100M Users':
                summary = "<b>Velocity:</b> Adoption is 40x faster. Value spreads instantly as distribution friction has vanished."
            elif m_name == 'Peak Infra Spend':
                summary = "<b>Conviction:</b> AI CapEx is nearly 15x larger than Cloud peaks, signaling massive global structural shifts."
            elif m_name == 'Rev per Employee':
                summary = "<b>Leverage:</b> AI is a Force Multiplier. It decouples revenue growth from headcount expansion."
            elif m_name == 'Startup Entry Cost':
                summary = "<b>Access:</b> Entry costs collapsed by 99.9%. Innovation is now democratized and hyper-affordable."
            
            st.markdown(f"""
                <div style="background-color: #F1F5F9; padding: 12px; border-radius: 6px; margin-top: -10px; margin-bottom: 20px; border-left: 3px solid #1E3A8A;">
                    <p style="font-size: 0.8rem; color: #1E293B; margin-bottom: 5px;">{summary}</p>
                    <p style="font-size: 0.7rem; color: #64748B; margin: 0;"><b>Source:</b> {row['Full_Source_Citations']}</p>
                </div>
            """, unsafe_allow_html=True)

    # --- 5. THE FACT SHEET (NO REPEAT HEADERS) ---
    st.markdown("##### Strategic Comparison Matrix")
    
    # Custom Navy Header
    st.markdown("""
        <div style="display: flex; background-color: #0F172A; padding: 15px 0px; border-radius: 8px 8px 0 0; width: 100%;">
            <div style="flex: 1.2; color: #FFFFFF; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; padding-left: 20px;">Metric</div>
            <div style="flex: 1; color: #94A3B8; font-weight: 700; font-size: 0.75rem; text-transform: uppercase;">Internet Era</div>
            <div style="flex: 1; color: #FFFFFF; font-weight: 700; font-size: 0.75rem; text-transform: uppercase;">SaaS Era</div>
            <div style="flex: 1; color: #38BDF8; font-weight: 800; font-size: 0.75rem; text-transform: uppercase;">AI Frontier</div>
            <div style="flex: 0.5; color: #FFFFFF; font-weight: 700; font-size: 0.75rem; text-transform: uppercase;">Unit</div>
        </div>
    """, unsafe_allow_html=True)

    # Setting column headers to None removes the second (Streamlit) header row
    st.dataframe(
        df_int[['Metric', 'Internet_Val', 'SaaS_Val', 'AI_Val', 'Unit']],
        column_config={
            "Metric": st.column_config.TextColumn(None, width="medium"),
            "Internet_Val": st.column_config.TextColumn(None),
            "SaaS_Val": st.column_config.TextColumn(None),
            "AI_Val": st.column_config.TextColumn(None),
            "Unit": st.column_config.TextColumn(None, width="small"),
        },
        hide_index=True,
        use_container_width=True,
        height=(len(df_int) * 36) + 40
    )

with tab6:
    st.subheader("1. Strategic Implementation: The Reality Check")
    
    # --- 1. CSS: DARK SELECTION TILES ---
    st.markdown("""
    <style>
        /* Container for wrapping tiles */
        div[data-testid="stRadio"] > div[role="radiogroup"] {
            gap: 12px;
            display: flex;
            flex-direction: row;
            flex-wrap: wrap;
        }
        /* Hide default circles */
        div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {
            display: none;
        }
        /* Unselected State */
        div[data-testid="stRadio"] > div[role="radiogroup"] > label {
            background-color: #F1F5F9 !important;
            border: 1px solid #E2E8F0 !important;
            padding: 10px 20px !important;
            border-radius: 6px !important;
            color: #475569 !important;
            transition: all 0.2s ease !important;
        }
        /* Hover State */
        div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
            border-color: #1E3A8A !important;
            background-color: #E2E8F0 !important;
        }
        /* Selected State - Dark Navy */
        div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"] {
            background-color: #0F172A !important; 
            border-color: #0F172A !important;
            color: #FFFFFF !important; 
            font-weight: 700 !important;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- 2. DATA CHECK & SELECTION ---
    if 'df_usecase' in locals() and not df_usecase.empty:
        all_industries = sorted(df_usecase['Industry'].unique().tolist())
        selected_industry = st.radio("Select Industry:", options=all_industries, horizontal=True, label_visibility="collapsed")
        
        # --- 3. DYNAMIC "CURRENT FOCUS" HEADER ---
        st.markdown(f"""
            <div style="margin-top: 25px; margin-bottom: 5px; display: flex; align-items: baseline;">
                <span style="color: #64748B; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.12em;">
                    Industry Context:
                </span>
                <span style="color: #0F172A; font-size: 1.4rem; font-weight: 800; margin-left: 10px; font-family: 'Helvetica Neue', sans-serif;">
                    {selected_industry}
                </span>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # --- 4. DATA FILTERING (Fixes the NameError) ---
        industry_data = df_usecase[df_usecase['Industry'] == selected_industry].copy()

        # --- 5. CARD RENDERING FUNCTION ---
        def render_executive_card(row, is_success=True):
            accent = "#16A34A" if is_success else "#DC2626"
            label = "VALIDATED SUCCESS" if is_success else "CRITICAL RISK"
            bg = "#F8FAFC"
            
            raw_name = str(row.get('Use Case', 'N/A'))
            clean_name = raw_name.replace("Best Case:", "").replace("Worst Case:", "").strip()
            
            st.markdown(f"""
            <div style="background-color: {bg}; border-left: 6px solid {accent}; padding: 22px; border-radius: 4px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="color: #1E3A8A; font-size: 1.3rem; font-weight: 800; margin-bottom: 12px; line-height: 1.2;">
                    {clean_name.upper()}
                </div>
                <div style="color: #334155; font-size: 1.05rem; line-height: 1.6; margin-bottom: 15px;">
                    {row.get('The "Why" (Technical/Business Reason)', 'N/A')}
                </div>
                <div style="border-top: 1px solid #E2E8F0; padding-top: 12px; display: flex; flex-direction: column; gap: 4px;">
                    <div style="font-size: 0.85rem; color: #475569;">
                        <b>STACK:</b> <span style="font-family: monospace; background: #F1F5F9; padding: 2px 6px; border-radius: 3px;">{row.get('Model/Tech Stack', 'N/A')}</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #94A3B8; font-style: italic;">
                        Source: {row.get('Citation', 'N/A')} ({row.get('Year', 'N/A')})
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


        # --- NEW: LARGE HEADERS ---
        header_col1, header_col2 = st.columns(2)
        with header_col1:
            st.markdown("<h2 style='color: #16A34A; font-size: 2rem; font-weight: 900; margin-bottom: 10px;'>VALIDATED SUCCESS</h2>", unsafe_allow_html=True)
        with header_col2:
            st.markdown("<h2 style='color: #DC2626; font-size: 2rem; font-weight: 900; margin-bottom: 10px;'>CRITICAL RISK</h2>", unsafe_allow_html=True)

        # --- 6. DISPLAY COLUMNS ---
        col_best, col_worst = st.columns(2)

        with col_best:
            best_cases = industry_data[industry_data['Verdict'].astype(str).str.lower().str.contains("best|success", regex=True)]
            if not best_cases.empty:
                for _, row in best_cases.iterrows():
                    render_executive_card(row, is_success=True)
            else:
                st.info(f"Gathering success stories for {selected_industry}...")

        with col_worst:
            worst_cases = industry_data[industry_data['Verdict'].astype(str).str.lower().str.contains("worst|fail", regex=True)]
            if not worst_cases.empty:
                for _, row in worst_cases.iterrows():
                    render_executive_card(row, is_success=False)
            else:
                st.info(f"Monitoring risk profiles for {selected_industry}...")

    st.markdown("---")

    # --- SECTION 2: THE DEFENSE (OBJECTIONS) ---
    st.markdown("### 2. The Objection Vault")
    st.write("Select a **Department**, then pick a **Stakeholder** to view the verified sales script.")

    if 'df_objections' in locals() and not df_objections.empty:
        
        # 1. PERSONA HIERARCHY
        persona_map = {
            "Risk & Legal": ["CISO", "Legal Counsel", "Compliance", "Security", "EU Counsel"],
            "Executive Leadership": ["CEO", "CFO", "Board Member", "Head of Sales"],
            "Engineering & Product": ["CTO", "VP of Engineering", "Data Engineer", "Product Manager"],
            "Operations & Support": ["Operations", "Support Manager"]
        }
        
        # 2. STEP 1:(Horizontal Row)
        st.markdown("<p style='color: #64748B; font-weight: 700; font-size: 0.8rem; margin-bottom: -10px;'>STEP 1: SELECT DEPARTMENT</p>", unsafe_allow_html=True)
        selected_group = st.radio(
            "Department:",
            options=list(persona_map.keys()),
            horizontal=True,
            label_visibility="collapsed",
            key="vault_group"
        )
        
        st.markdown("<hr style='margin: 15px 0; border: 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
        
        # 3. STEP 2: STAKEHOLDER ROLE (Filtered Horizontal Row)
        potential_roles = persona_map[selected_group]
        valid_roles = [r for r in potential_roles if r in df_objections['Customer Role'].unique()]
        
        if not valid_roles:
            valid_roles = df_objections['Customer Role'].unique()

        st.markdown("<p style='color: #64748B; font-weight: 700; font-size: 0.8rem; margin-bottom: -10px;'>STEP 2: SELECT STAKEHOLDER ROLE</p>", unsafe_allow_html=True)
        selected_role = st.radio(
            "Select Role:",
            options=valid_roles,
            horizontal=True,
            label_visibility="collapsed",
            key="vault_role"
        )
        
        # Extract specific data
        role_data = df_objections[df_objections['Customer Role'] == selected_role].iloc[0]

        # FIX 1: Remove double-double quotes from all text fields
        role_data = role_data.apply(lambda x: str(x).replace('"', '').strip())

        # 4. THE BATTLE CARD (The Hero Content)
        st.markdown(f"""
            <div style="margin-top: 30px; margin-bottom: 20px;">
                <h2 style="color: #0F172A; font-size: 1.8rem; font-weight: 900; border-left: 8px solid #1E3A8A; padding-left: 15px; line-height: 1.2;">
                    DEPARTMENT: {selected_group.upper()} <br>
                    STAKEHOLDER: {selected_role.upper()}
                </h2>
                <p style="color: #64748B; font-size: 1.1rem; font-weight: 500; margin-top: 10px;">
                    Primary Concern: <span style="color: #DC2626; font-weight: 700;">{role_data['The Obstacle']}</span>
                </p>
                <div style="color: #991B1B; font-size: 0.75rem; font-style: italic; border-top: 1px solid #FEE2E2; padding-top: 10px;">
                    Source: {role_data['Refined Source']}
                    </div>
            </div>
        """, unsafe_allow_html=True)

        # 5. OBJECTION VS RESPONSE (High-Impact Columns)
        obj_col, resp_col = st.columns(2)

        with obj_col:
            st.markdown("<h2 style='color: #DC2626; font-size: 1.8rem; font-weight: 900;'>THE OBJECTION</h2>", unsafe_allow_html=True)
            st.markdown(f"""
                <div style="background-color: #FEF2F2; border: 1px solid #FEE2E2; padding: 20px; border-radius: 8px; min-height: 220px; display: flex; flex-direction: column; justify-content: space-between;">
                    <p style="color: #7F1D1D; font-size: 1.4rem; font-weight: 500;">
                        {role_data['The Sales Objection']}
                    </p>
                </div>
            """, unsafe_allow_html=True)

        with resp_col:
            st.markdown("<h2 style='color: #16A34A; font-size: 1.8rem; font-weight: 900;'>THE WINNING SCRIPT</h2>", unsafe_allow_html=True)
            st.markdown(f"""
                <div style="background-color: #F0FDF4; border: 1px solid #DCFCE7; padding: 20px; border-radius: 8px; min-height: 220px; display: flex; flex-direction: column; justify-content: space-between;">
                    <p style="color: #14532D; font-size: 1.4rem; font-weight: 500;">
                        {role_data['The Winning Response (Solution)']}
                    </p>
                </div>
            """, unsafe_allow_html=True)
