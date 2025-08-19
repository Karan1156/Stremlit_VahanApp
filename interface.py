import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# Set page config with a more professional color scheme
st.set_page_config(
    page_title="VahanHelpDashboard",
    layout="wide",
    page_icon="🚗"
)

# Custom CSS for better visual styling
st.markdown("""
    <style>
        /* Main color scheme */
        :root {
            --primary: #4a6fa5;
            --secondary: #166088;
            --accent: #4fc3f7;
            --background: #f8f9fa;
            --text: #333333;
            --success: #28a745;
            --warning: #ffc107;
            --danger: #dc3545;
        }
        
        /* Metric cards */
        .stMetric {
            border-left: 4px solid var(--primary);
            border-radius: 4px;
            padding: 15px;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            color: black !important;
        }
        
        /* White box text color */
        .stExpander, .stDataFrame, .stMetric, .stMarkdown {
            color: black !important;
        }
        
        /* Dataframes */
        .stDataFrame {
            font-size: 14px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Expanders */
        .stExpander {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            background-color: white;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: var(--primary) !important;
        }
        
        /* Tabs */
        .stTabs [role="tablist"] {
            border-bottom: 2px solid var(--primary);
        }
        .stTabs [aria-selected="true"] {
            color: var(--primary) !important;
            font-weight: bold;
            border-bottom: 3px solid var(--accent);
        }
        
        /* Scrollable container */
        @media (max-width: 768px) {
            .client-scroll {
                overflow-x: auto;
                white-space: nowrap;
                padding-bottom: 10px;
            }
        }
    </style>
""", unsafe_allow_html=True)

# Color palette for consistent visualization colors
COLOR_PALETTE = {
    'Total Sale': '#4a6fa5',  
    'Total Cost': '#166088',  
    'Total Difference': '#4fc3f7',  
    'Revenue': '#28a745',   
    'Expense': '#dc3545',     
    'Profit': '#17a2b8',      
    'Case Count': '#6c757d'
}

# Function to format Indian rupees
def format_rupees(amount):
    return f"₹{amount:,.2f}"

# Function to format rupees for short display (in lakhs/crores)
def format_rupees_short(amount):
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.1f}Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.1f}L"
    elif amount >= 1000:  # 1 thousand
        return f"₹{amount/1000:.1f}K"
    else:
        return f"₹{amount:,.0f}"

# Function to fetch data from API
def fetch_data():
    try:
        response = requests.get("https://vahan-help.onrender.com/")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch data. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {e}")
        return None

# Main app
def main():
    st.title("🚗 Car Transfer/NOC Management System")
    
    # Fetch data
    data_list = fetch_data()
    
    if data_list and isinstance(data_list, list):
        # Create a dataframe
        df = pd.DataFrame(data_list)
        
        # Convert date columns to datetime
        date_cols = ['transferDate', 'NOCissuedDate', 'Invoice Date']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Sidebar filters with consistent styling
        st.sidebar.header("🔍 Filter Cases")
        st.sidebar.markdown("---")
        
        # Car Number filter
        car_numbers = ['All'] + sorted(df['Car Number'].unique().tolist())
        selected_car = st.sidebar.selectbox("Car Number", car_numbers)
        
        # Client Name filter
        client_names = ['All'] + sorted(df['Client Name'].unique().tolist())
        selected_client = st.sidebar.selectbox("Client Name", client_names)
        
        # Case Type filter
        case_types = ['All'] + sorted(df['Case Type'].unique().tolist())
        selected_case_type = st.sidebar.selectbox("Case Type", case_types)
        
        # Status filter
        statuses = ['All'] + sorted(df['Buyer payment'].unique().tolist())
        selected_status = st.sidebar.selectbox("Payment Status", statuses)
        
        # Date range filter
        if 'transferDate' in df.columns:
            min_date = df['transferDate'].min()
            max_date = df['transferDate'].max()
            date_range = st.sidebar.date_input(
                "Transfer Date Range",
                [min_date, max_date],
                min_value=min_date,
                max_value=max_date
            )
        
        # Apply filters
        filtered_df = df.copy()
        if selected_car != 'All':
            filtered_df = filtered_df[filtered_df['Car Number'] == selected_car]
        if selected_client != 'All':
            filtered_df = filtered_df[filtered_df['Client Name'] == selected_client]
        if selected_case_type != 'All':
            filtered_df = filtered_df[filtered_df['Case Type'] == selected_case_type]
        if selected_status != 'All':
            filtered_df = filtered_df[filtered_df['Buyer payment'] == selected_status]
        if 'transferDate' in df.columns and len(date_range) == 2:
            filtered_df = filtered_df[
                (filtered_df['transferDate'] >= pd.to_datetime(date_range[0])) &
                (filtered_df['transferDate'] <= pd.to_datetime(date_range[1]))
            ]
        
        # ==================================
        # QUARTERLY FINANCIAL DASHBOARD
        # ==================================
        st.header("📈 Quarterly Financial Dashboard")
        
        if not filtered_df.empty and 'transferDate' in filtered_df.columns:
            # Create quarter column
            filtered_df['Quarter'] = filtered_df['transferDate'].dt.to_period('Q').astype(str)
            
            # Group by quarter for financial metrics
            quarterly_data = filtered_df.groupby('Quarter').agg({
                'Total Sale': 'sum',
                'Total Cost': 'sum',
                'Total Difference': 'sum',
                'Car Number': 'count'
            }).reset_index().rename(columns={'Car Number': 'Case Count'})
            
            # Create tabs for different views
            tab1, tab2 = st.tabs(["Financial Metrics", "Client Analysis"])
            
            with tab1:
                # Quarterly Financial Metrics
                st.subheader("Quarterly Financial Performance")
                
                # Vertical bar chart with consistent colors
                fig = px.bar(
                    quarterly_data.melt(id_vars='Quarter', 
                                     value_vars=['Total Sale', 'Total Cost', 'Total Difference'],
                                     var_name='Metric', 
                                     value_name='Amount'),
                    y='Quarter',
                    x='Amount',
                    color='Metric',
                    color_discrete_map={
                        'Total Sale': COLOR_PALETTE['Total Sale'],
                        'Total Cost': COLOR_PALETTE['Total Cost'],
                        'Total Difference': COLOR_PALETTE['Total Difference']
                    },
                    barmode='group',
                    title='Quarterly Sales, Costs, and Profits',
                    labels={'Amount': 'Amount (₹)'},
                    orientation='h',
                    height=500
                )
                fig.update_layout(
                    yaxis={'categoryorder':'total ascending'},
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Line chart with consistent colors
                fig = px.line(
                    quarterly_data,
                    x='Quarter',
                    y=['Total Sale', 'Total Cost', 'Total Difference'],
                    title='Financial Trends Over Quarters',
                    labels={'value': 'Amount (₹)', 'variable': 'Metric'},
                    color_discrete_map={
                        'Total Sale': COLOR_PALETTE['Total Sale'],
                        'Total Cost': COLOR_PALETTE['Total Cost'],
                        'Total Difference': COLOR_PALETTE['Total Difference']
                    }
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Quarterly metrics with colored cards
                st.subheader("Quarterly Summary")
                cols = st.columns(len(quarterly_data))
                for idx, (_, row) in enumerate(quarterly_data.iterrows()):
                    with cols[idx]:
                        st.markdown(
                            f"""
                            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; 
                                        border-left: 4px solid {COLOR_PALETTE['Total Sale']}; 
                                        margin-bottom: 10px;">
                                <h4 style="color: {COLOR_PALETTE['Total Sale']}; margin-top: 0;">Q{row['Quarter'][-1]} {row['Quarter'][:4]}</h4>
                                <p style="font-size: 24px; font-weight: bold; margin-bottom: 5px; color: black;">{format_rupees(row['Total Sale'])}</p>
                                <p style="color: {COLOR_PALETTE['Total Difference']}; margin: 0; color: black;">Profit: {format_rupees(row['Total Difference'])}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            
            with tab2:
                # Client-wise Analysis
                st.subheader("Client Performance Analysis")
                
                # Client-wise case count
                client_case_count = filtered_df['Client Name'].value_counts().reset_index()
                client_case_count.columns = ['Client Name', 'Case Count']
                
                # Make client analysis scrollable on small screens
                st.markdown('<div class="client-scroll">', unsafe_allow_html=True)
                
                # Modified bar chart with case counts on bars and increased width
                fig = px.bar(
                    client_case_count,
                    y='Client Name',
                    x='Case Count',
                    title='Clients by Case Volume',
                    text='Case Count',  # Display case count on bars
                    color='Client Name',
                    orientation='h',
                    height=max(500, len(client_case_count) * 30),
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                
                # Update layout for better visualization
                fig.update_layout(
                    yaxis={'categoryorder':'total ascending'},
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    uniformtext_minsize=12,  # Minimum font size for text
                    uniformtext_mode='hide',  # Hide text if it doesn't fit
                    bargap=0.2,  # Gap between bars
                    bargroupgap=0.1  # Gap between bar groups
                )
                
                # Increase bar width and adjust text position
                fig.update_traces(
                    width=0.8,  # Increased bar width (default is 0.8 for categorical data)
                    textposition='outside',  # Position text outside the bars
                    texttemplate='%{text}',  # Display the exact case count
                    marker_line_color='rgb(8,48,107)',
                    marker_line_width=1.5,
                    opacity=0.8
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Client-wise financial performance
                client_finance = filtered_df.groupby('Client Name').agg({
                    'Total Sale': 'sum',
                    'Total Cost': 'sum',
                    'Total Difference': 'sum',
                    'Car Number': 'count'
                }).reset_index().rename(columns={'Car Number': 'Case Count'})
                
                # Create scatter plot with enhanced data labels
                st.subheader("Client Financial Performance")
                
                fig = px.scatter(
                    client_finance,
                    x='Case Count',
                    y='Total Difference',
                    size='Total Sale',
                    color='Client Name',
                    hover_name='Client Name',
                    title='Client Performance: Case Count vs Profit',
                    labels={
                        'Total Difference': 'Total Profit (₹)', 
                        'Case Count': 'Number of Cases',
                        'Total Sale': 'Total Sales Amount'
                    },
                    hover_data=['Total Sale', 'Total Cost'],
                    color_discrete_sequence=px.colors.qualitative.Set3,
                    size_max=60
                )
                
                # Add annotations for each point with client name and profit
                for i, row in client_finance.iterrows():
                    fig.add_annotation(
                        x=row['Case Count'],
                        y=row['Total Difference'],
                        text=f"<b>{row['Client Name']}</b><br>{format_rupees_short(row['Total Difference'])}",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=2,
                        arrowcolor="rgba(0,0,0,0.5)",
                        ax=0,
                        ay=-40,
                        bgcolor="rgba(255,255,255,0.9)",
                        bordercolor="rgba(0,0,0,0.3)",
                        borderwidth=1,
                        font=dict(size=10, color="black"),
                        align="center"
                    )
                
                fig.update_traces(
                    hovertemplate="<b>%{hovertext}</b><br><br>" +
                    "Cases: %{x}<br>" +
                    "Profit: ₹%{y:,.2f}<br>" +
                    "Sales: ₹%{customdata[0]:,.2f}<br>" +
                    "Costs: ₹%{customdata[1]:,.2f}<extra></extra>",
                    marker=dict(
                        line=dict(width=2, color='DarkSlateGrey'),
                        opacity=0.8
                    )
                )
                
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    height=600,
                    margin=dict(t=80, b=80, l=80, r=80)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Enhanced Client Financial Summary Bar Chart
                st.subheader("Client Financial Summary")
                
                # Sort clients by total sale for better visualization
                client_finance_sorted = client_finance.sort_values('Total Sale', ascending=True)
                
                # Create horizontal bar chart for better readability
                fig = px.bar(
                    client_finance_sorted,
                    y='Client Name',
                    x='Total Sale',
                    title='Client Revenue Overview',
                    labels={'Total Sale': 'Total Sales (₹)', 'Client Name': 'Client'},
                    color='Total Sale',
                    color_continuous_scale='Blues',
                    orientation='h',
                    height=max(400, len(client_finance_sorted) * 50)
                )
                
                # Add data labels on bars
                for i, row in client_finance_sorted.iterrows():
                    fig.add_annotation(
                        x=row['Total Sale'],
                        y=row['Client Name'],
                        text=f"<b>{format_rupees_short(row['Total Sale'])}</b>",
                        showarrow=False,
                        xanchor="left",
                        xshift=10,
                        font=dict(size=11, color="black", family="Arial Black"),
                        bgcolor="rgba(255,255,255,0.8)",
                        bordercolor="rgba(0,0,0,0.2)",
                        borderwidth=1,
                        borderpad=2
                    )
                
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)'),
                    yaxis=dict(showgrid=False),
                    margin=dict(l=150, r=100, t=80, b=50)
                )
                
                fig.update_traces(
                    marker=dict(
                        line=dict(width=1, color='rgba(0,0,0,0.3)'),
                        opacity=0.8
                    ),
                    hovertemplate="<b>%{y}</b><br>" +
                    "Total Sales: ₹%{x:,.2f}<extra></extra>"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Profit vs Cost Comparison Chart
                st.subheader("Profit vs Cost Analysis")
                
                # Create subplot for profit vs cost
                fig = px.bar(
                    client_finance_sorted,
                    y='Client Name',
                    x=['Total Difference', 'Total Cost'],
                    title='Client Profitability Analysis',
                    labels={'value': 'Amount (₹)', 'variable': 'Type'},
                    color_discrete_map={
                        'Total Difference': COLOR_PALETTE['Total Difference'],
                        'Total Cost': COLOR_PALETTE['Total Cost']
                    },
                    orientation='h',
                    barmode='group',
                    height=max(400, len(client_finance_sorted) * 50)
                )
                
                # Add data labels for both profit and cost
                for i, row in client_finance_sorted.iterrows():
                    # Profit label
                    fig.add_annotation(
                        x=row['Total Difference'],
                        y=i + 0.15,  # Slight offset for profit bar
                        text=f"<b>P: {format_rupees_short(row['Total Difference'])}</b>",
                        showarrow=False,
                        xanchor="left" if row['Total Difference'] > 0 else "right",
                        xshift=10 if row['Total Difference'] > 0 else -10,
                        font=dict(size=9, color=COLOR_PALETTE['Total Difference'], family="Arial Bold"),
                        bgcolor="rgba(255,255,255,0.9)",
                        bordercolor=COLOR_PALETTE['Total Difference'],
                        borderwidth=1
                    )
                    
                    # Cost label
                    fig.add_annotation(
                        x=row['Total Cost'],
                        y=i - 0.15,  # Slight offset for cost bar
                        text=f"<b>C: {format_rupees_short(row['Total Cost'])}</b>",
                        showarrow=False,
                        xanchor="left",
                        xshift=10,
                        font=dict(size=9, color=COLOR_PALETTE['Total Cost'], family="Arial Bold"),
                        bgcolor="rgba(255,255,255,0.9)",
                        bordercolor=COLOR_PALETTE['Total Cost'],
                        borderwidth=1
                    )
                
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)'),
                    yaxis=dict(showgrid=False),
                    margin=dict(l=150, r=150, t=80, b=50),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # ======================
        # EXISTING FUNCTIONALITY
        # ======================
        
        st.header("📋 Filtered Transfer Cases")
        
        # Format currency columns
        display_df = filtered_df.copy()
        if 'Total Cost' in display_df.columns:
            display_df['Total Cost'] = display_df['Total Cost'].apply(format_rupees)
        if 'Total Sale' in display_df.columns:
            display_df['Total Sale'] = display_df['Total Sale'].apply(format_rupees)
        
        # Create a simplified dataframe for the overview
        overview_df = display_df[[
            'Car Number', 'Client Name', 'Case Type', 'Task Type', 
            'transferDate', 'Total Cost', 'Total Sale', 'Buyer payment'
        ]].rename(columns={'Buyer payment': 'Status'})
        
        # Apply conditional formatting to the dataframe
        def color_status(val):
            if val == 'Done':
                return 'color: #28a745; font-weight: bold;'  # Green
            elif val == 'Pending':
                return 'color: #ffc107; font-weight: bold;'  # Yellow
            else:
                return ''
        
        styled_df = overview_df.style.applymap(color_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Show statistics with proper rupee formatting and colored cards
        st.subheader("📊 Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; 
                            border-left: 4px solid {COLOR_PALETTE['Total Sale']}; 
                            margin-bottom: 10px;">
                    <h4 style="color: {COLOR_PALETTE['Total Sale']}; margin-top: 0;">Total Cases</h4>
                    <p style="font-size: 24px; font-weight: bold; margin-bottom: 5px; color: black;">{len(filtered_df)}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            total_cost = filtered_df['Total Cost'].sum()
            st.markdown(
                f"""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; 
                            border-left: 4px solid {COLOR_PALETTE['Total Cost']}; 
                            margin-bottom: 10px;">
                    <h4 style="color: {COLOR_PALETTE['Total Cost']}; margin-top: 0;">Total Cost</h4>
                    <p style="font-size: 24px; font-weight: bold; margin-bottom: 5px; color: black;">{format_rupees(total_cost)}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col3:
            total_sale = filtered_df['Total Sale'].sum()
            st.markdown(
                f"""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; 
                            border-left: 4px solid {COLOR_PALETTE['Total Sale']}; 
                            margin-bottom: 10px;">
                    <h4 style="color: {COLOR_PALETTE['Total Sale']}; margin-top: 0;">Total Sale</h4>
                    <p style="font-size: 24px; font-weight: bold; margin-bottom: 5px; color: black;">{format_rupees(total_sale)}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Case Details Section
        st.divider()
        st.subheader("🔍 View Case Details")
        
        if len(filtered_df) > 0:
            case_options = [
                f"{row['Car Number']} - {row['Client Name']}" 
                for _, row in filtered_df.iterrows()
            ]
            selected_case = st.selectbox("Select a case to view details:", case_options)
            
            # Find the selected case
            selected_index = case_options.index(selected_case)
            data = filtered_df.iloc[selected_index].to_dict()
            
            # Display detailed view with improved styling
            with st.expander(f"Detailed View: {data.get('Car Number', 'N/A')}", expanded=True):
                # Display basic info in columns
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Car Number:** {data.get('Car Number', 'N/A')}")
                    st.markdown(f"**Client Name:** {data.get('Client Name', 'N/A')}")
                    
                with col2:
                    st.markdown(f"**Case Type:** {data.get('Case Type', 'N/A')}")
                    st.markdown(f"**Task Type:** {data.get('Task Type', 'N/A')}")
                    st.markdown(f"**Additional Work:** {data.get('Additional Work', 'N/A')}")
                    
                with col3:
                    st.markdown(f"**Seller RTO:** {data.get('Seller RTO', 'N/A')}")
                    st.markdown(f"**Buyer RTO:** {data.get('Buyer RTO', 'N/A')}")
                
                # Timeline section
                st.divider()
                st.subheader("📅 Timeline")
                timeline_col1, timeline_col2 = st.columns(2)
                
                with timeline_col1:
                    st.markdown(f"**Transfer Date:** {data.get('transferDate', 'N/A')}")
                with timeline_col2:
                    st.markdown(f"**NOC Issued Date:** {data.get('NOCissuedDate', 'N/A')}")
                
                # Financial information
                st.divider()
                st.subheader("💰 Financial Details")
                
                # Cost breakdown
                cost_col1, cost_col2, cost_col3 = st.columns(3)
                with cost_col1:
                    st.markdown("**Cost Breakdown**")
                    st.write(data.get('Cost', 'N/A'))
                with cost_col2:
                    st.markdown("**Sale Breakdown**")
                    st.write(data.get('Sale', 'N/A'))
                with cost_col3:
                    st.markdown("**Summary**")
                    st.markdown(
                        f"""
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; 
                                    border-left: 4px solid {COLOR_PALETTE['Total Cost']}; 
                                    margin-bottom: 10px;">
                            <p style="font-size: 16px; margin: 0; color: black;">Total Cost</p>
                            <p style="font-size: 20px; font-weight: bold; margin: 0; color: black;">{format_rupees(data.get('Total Cost', 0))}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f"""
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; 
                                    border-left: 4px solid {COLOR_PALETTE['Total Sale']}; 
                                    margin-bottom: 10px;">
                            <p style="font-size: 16px; margin: 0; color: black;">Total Sale</p>
                            <p style="font-size: 20px; font-weight: bold; margin: 0; color: black;">{format_rupees(data.get('Total Sale', 0))}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f"""
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; 
                                    border-left: 4px solid {COLOR_PALETTE['Total Difference']}; 
                                    margin-bottom: 10px;">
                            <p style="font-size: 16px; margin: 0; color: black;">Profit</p>
                            <p style="font-size: 20px; font-weight: bold; margin: 0; color: black;">{format_rupees(data.get('Total Difference', 0))}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                # Payment status
                st.divider()
                st.subheader("💳 Payment Status")
                pay_col1, pay_col2, pay_col3 = st.columns(3)
                with pay_col1:
                    payment_status = data.get('Seller payment', 'N/A')
                    color = '#28a745' if payment_status == 'Done' else '#ffc107'
                    st.markdown(f"**Seller Payment:** <span style='color: {color}; font-weight: bold;'>{payment_status}</span>", unsafe_allow_html=True)
                    st.markdown(f"**UTR:** {data.get('Seller UTR', 'N/A')}")
                with pay_col2:
                    payment_status = data.get('Buyer payment', 'N/A')
                    color = '#28a745' if payment_status == 'Done' else '#ffc107'
                    st.markdown(f"**Buyer Payment:** <span style='color: {color}; font-weight: bold;'>{payment_status}</span>", unsafe_allow_html=True)
                    st.markdown(f"**UTR:** {data.get('Buyer UTR', 'N/A')}")
                with pay_col3:
                    st.markdown(f"**Bill Generated:** {data.get('Bill Generated', 'N/A')}")
                    st.markdown(f"**Amount Status:** {data.get('Amount Status', 'N/A')}")
                
                # Agent information
                st.divider()
                st.subheader("👤 Agent Information")
                agent_col1, agent_col2 = st.columns(2)
                with agent_col1:
                    st.markdown(f"**Seller Side Agent:** {data.get('Seller Side Agent', 'N/A')}")
                with agent_col2:
                    st.markdown(f"**Buyer Side Agent:** {data.get('Buyer Side Agent', 'N/A')}")
                
                # Additional information
                st.divider()
                st.subheader("📄 Documents")
                doc_col1, doc_col2, doc_col3 = st.columns(3)
                with doc_col1:
                    st.markdown(f"**Invoice Number:** {data.get('Invoice Number', 'N/A')}")
                with doc_col2:
                    st.markdown(f"**Invoice Date:** {data.get('Invoice Date', 'N/A')}")
                with doc_col3:
                    st.markdown(f"**Receipt:** {data.get('Receipt', 'N/A')}")
        else:
            st.warning("No cases match your filters")
        
        # Display raw data (for debugging)
        if st.checkbox("Show raw data for all cases"):
            st.json(data_list)
    elif data_list:
        st.warning("Unexpected data format received from API")
    else:
        st.warning("No data available or failed to fetch data.")

if __name__ == "__main__":
    main()