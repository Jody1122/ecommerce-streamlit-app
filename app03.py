import streamlit as st
import pandas as pd
import requests
import altair as alt
import boto3
import os

# Function to load AWS credentials from a file
def load_aws_credentials(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                key, value = line.strip().split('=')
                os.environ[key] = value
        print("AWS credentials loaded successfully.")
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        exit(1)
    except Exception as e:
        print(f"Error reading the credentials file: {e}")
        exit(1)

# Load AWS credentials
credentials_file_path = '/home/ubuntu/aws_credentials.txt'  # Path on your EC2 instance
load_aws_credentials(credentials_file_path)

# Initialize Boto3 client using the loaded credentials
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

# Function to fetch data from the Flask API in batches
def fetch_data_batch(api_url, batch_size, batch_number):
    params = {'batch_size': batch_size, 'batch_number': batch_number}
    response = requests.get(api_url, params=params)
    data = response.json()

    # Convert the dictionary directly into a DataFrame
    df = pd.DataFrame(data)
    
    return df

# Parameters for batch processing
batch_size = 10000
batch_number = 0

# API endpoint
api_url = 'http://ec2-18-191-222-181.us-east-2.compute.amazonaws.com:8510/get_processed_data'

# Initialize an empty DataFrame
all_batches_df = pd.DataFrame()

# Fetch and combine data in batches
while True:
    batch_df = fetch_data_batch(api_url, batch_size, batch_number)
    if batch_df.empty:
        break  # Stop if no more data is returned
    all_batches_df = pd.concat([all_batches_df, batch_df], ignore_index=True)
    batch_number += 1

df = all_batches_df

# Your existing Streamlit visualization code
st.title("Ecommerce Data Exploration")

# Filter options
st.sidebar.header("Filter Options")
selected_outliers = st.sidebar.selectbox("Outliers", options=df['outlier'].unique())
selected_outlier_knn = st.sidebar.selectbox("KNN Outliers", options=df['outlier_knn'].unique())
selected_months = st.sidebar.multiselect("Select months", options=df['month'].unique(), default=df['month'].unique())
selected_market = st.sidebar.multiselect("Select marketplace", options=df['marketplace'].unique(), default=df['marketplace'].unique())
selected_days_of_week = st.sidebar.multiselect("Select days of the week", options=df['day_of_week'].unique(), default=df['day_of_week'].unique())

# Apply filters
filtered_df = df[(df['outlier'] == selected_outliers) & 
                 (df['outlier_knn'] == selected_outlier_knn) & 
                 (df['month'].isin(selected_months)) &
                 (df['marketplace'].isin(selected_market)) &
                 (df['day_of_week'].isin(selected_days_of_week))]

# Display filtered DataFrame
st.write(filtered_df)

# Distribution of Outliers by Month
st.subheader("Distribution of Outliers by Month")
month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
outliers_by_month = filtered_df['month_name'].value_counts().reindex(month_order, fill_value=0).reset_index()
outliers_by_month.columns = ['month_name', 'count']
chart = alt.Chart(outliers_by_month).mark_bar(color='lightblue').encode(
    x=alt.X('month_name', sort=month_order),
    y='count'
).properties(
    width=alt.Step(40)  # controls the width of bar.
)
st.altair_chart(chart, use_container_width=True)

# Distribution of Outliers by Day of the Week
st.subheader("Distribution of Outliers by Day of the Week")
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
outliers_by_day_of_week = filtered_df['day_name'].value_counts().reindex(day_order, fill_value=0).reset_index()
outliers_by_day_of_week.columns = ['day_name', 'count']
chart = alt.Chart(outliers_by_day_of_week).mark_bar(color='darkblue').encode(
    x=alt.X('day_name', sort=day_order),
    y='count'
).properties(
    width=alt.Step(40)  # controls the width of bar.
)
st.altair_chart(chart, use_container_width=True)

# Distribution of Outliers by Market
st.subheader("Distribution of Outliers by Market")
outliers_by_market = filtered_df['marketplace'].value_counts().reset_index()
outliers_by_market.columns = ['marketplace', 'count']
chart = alt.Chart(outliers_by_market).mark_bar(color='#005f73').encode(
    x='marketplace',
    y='count'
).properties(
    width=alt.Step(40)  # controls the width of bar.
)
st.altair_chart(chart, use_container_width=True)
