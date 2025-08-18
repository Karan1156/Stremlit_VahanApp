import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# Set page config
st.set_page_config(page_title="Car Transfer/NOC Tracker", layout="wide")

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
        
        # Sidebar filters
        st.sidebar.header("🔍 Filter Cases")
        
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
        # NEW: QUARTERLY FINANCIAL DASHBOARD
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
                
                # Bar chart for quarterly comparison
                fig = px.bar(
                    quarterly_data.melt(id_vars='Quarter', 
                                     value_vars=['Total Sale', 'Total Cost', 'Total Difference'],
                                     var_name='Metric', 
                                     value_name='Amount'),
                    x='Quarter',
                    y='Amount',
                    color='Metric',
                    barmode='group',
                    title='Quarterly Sales, Costs, and Profits',
                    labels={'Amount': 'Amount (₹)'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Line chart for trend analysis
                fig = px.line(
                    quarterly_data,
                    x='Quarter',
                    y=['Total Sale', 'Total Cost', 'Total Difference'],
                    title='Financial Trends Over Quarters',
                    labels={'value': 'Amount (₹)', 'variable': 'Metric'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Quarterly metrics
                st.subheader("Quarterly Summary")
                cols = st.columns(len(quarterly_data))
                for idx, (_, row) in enumerate(quarterly_data.iterrows()):
                    with cols[idx]:
                        st.metric(f"Q{row['Quarter'][-1]} {row['Quarter'][:4]}", 
                                 f"₹{row['Total Sale']:,.0f}",
                                 delta=f"Profit: ₹{row['Total Difference']:,.0f}")
            
            with tab2:
                # Client-wise Analysis
                st.subheader("Client Performance Analysis")
                
                # Client-wise case count
                client_case_count = filtered_df['Client Name'].value_counts().reset_index()
                client_case_count.columns = ['Client Name', 'Case Count']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(
                        client_case_count.head(10),
                        x='Client Name',
                        y='Case Count',
                        title='Top 10 Clients by Case Volume',
                        color='Client Name'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.pie(
                        client_case_count,
                        names='Client Name',
                        values='Case Count',
                        title='Client Distribution by Case Volume'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Client-wise financial performance
                client_finance = filtered_df.groupby('Client Name').agg({
                    'Total Sale': 'sum',
                    'Total Cost': 'sum',
                    'Total Difference': 'sum',
                    'Car Number': 'count'
                }).reset_index().rename(columns={'Car Number': 'Case Count'})
                
                st.subheader("Client Financial Performance")
                fig = px.scatter(
                    client_finance,
                    x='Case Count',
                    y='Total Difference',
                    size='Total Sale',
                    color='Client Name',
                    hover_name='Client Name',
                    title='Client Performance: Case Count vs Profit',
                    labels={'Total Difference': 'Total Profit (₹)', 'Case Count': 'Number of Cases'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # ======================
        # EXISTING FUNCTIONALITY
        # ======================
        
        st.header("📋 Filtered Transfer Cases")
        
        # Create a simplified dataframe for the overview
        overview_df = filtered_df[[
            'Car Number', 'Client Name', 'Case Type', 'Task Type', 
            'transferDate', 'Total Cost', 'Total Sale', 'Buyer payment'
        ]].rename(columns={'Buyer payment': 'Status'})
        
        st.dataframe(overview_df, use_container_width=True)
        
        # Show statistics
        st.subheader("📊 Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Cases", len(filtered_df))
        with col2:
            total_cost = filtered_df['Total Cost'].sum()
            st.metric("Total Cost", f"₹{total_cost:,.2f}")
        with col3:
            total_sale = filtered_df['Total Sale'].sum()
            st.metric("Total Sale", f"₹{total_sale:,.2f}")
        
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
            
            # Display detailed view
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
                    st.metric("Total Cost", f"₹{data.get('Total Cost', 0)}")
                    st.metric("Total Sale", f"₹{data.get('Total Sale', 0)}")
                    st.metric("Profit", f"₹{data.get('Total Difference', 0)}", delta_color="normal")
                
                # Payment status
                st.divider()
                st.subheader("💳 Payment Status")
                pay_col1, pay_col2, pay_col3 = st.columns(3)
                with pay_col1:
                    st.markdown(f"**Seller Payment:** {data.get('Seller payment', 'N/A')}")
                    st.markdown(f"**UTR:** {data.get('Seller UTR', 'N/A')}")
                with pay_col2:
                    st.markdown(f"**Buyer Payment:** {data.get('Buyer payment', 'N/A')}")
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