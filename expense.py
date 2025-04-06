import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go   
from datetime import timedelta


#Setting up Streamlit Web App
st.set_page_config(
    page_title ='Finance Tracker',
    page_icon = '💙',
    layout = 'wide'
)
#title
st.title("Student Personal Finance Tracker")

# I am doing data cleaning here
def clean_data(df):
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
    df.columns = df.columns.str.strip()
    df['Daily Total'] = df['Daily Total'].astype(float)
    df['Month'] = df['Date'].dt.month_name()
    df['Day'] = df['Day'].str.strip()
    df.fillna(0, inplace=True)
    if 'Unnamed: 11' in df.columns:
        df = df.drop(columns=['Unnamed: 11'])
    return df

#Here we are taking the csv input from the user. If the user does not gives an input we show analysis on default finance csv data
with st.sidebar:
    st.markdown("## **Let's Start!**")

    uploaded_file = st.file_uploader("📂 Upload your Expense CSV", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.success("✅ File uploaded successfully!")
    else:
        df = pd.read_csv('Finance_data.csv')
        st.info("Using default data: Finance_data.csv")

    df = clean_data(df)

    with st.expander("📄 Need a sample template?"):
        st.markdown("""
        Here is a free **Expense Tracker Template** to help you get started.
        
        Fill it in and upload to see the analysis or upload your own CSV, just keep columns like **Date**, **Day**,**Income**, and **Daily Total** the same for best results.

        You can either keep the expense category columns (Bills, Education etc) as it is or remove them. You can also create your own categories. 
        """)

        with open("expense_temp.xlsx", "rb") as file:
            st.download_button(
                label="📥 Download Expense Template",
                data=file,
                file_name="Expense_Template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


#filters
month_options = ['All'] + sorted(df['Month'].unique()) 
selected_month = st.sidebar.selectbox("Select the Month", month_options)

# Filter Data Based on Month Selection
if selected_month == "All":
    filtered_df = df.copy()  
else:
    filtered_df = df[df['Month'] == selected_month]

# Day Filter 
day_options = ['All'] + sorted(filtered_df['Day'].unique())
selected_day = st.sidebar.selectbox("Select the Day", day_options)

# Filter Data Based on Day Selection
if selected_day != "All":
    filtered_df = filtered_df[filtered_df['Day'] == selected_day]

# Automatically detect category columns
non_category_cols = ['Date', 'Day', 'Daily Total', 'Month', 'Income','Income Source']
category_cols = [col for col in df.columns if col not in non_category_cols and df[col].dtype in ['int64', 'float64']]


# Sidebar category filter (single select)
selected_category = st.sidebar.selectbox(
    "View metrics and charts for a specific category:",
    ["All Categories"] + category_cols
)
# Filter data further if a specific category is selected
if selected_category != "All Categories":
    category_df = filtered_df[["Date", selected_category]].copy()
    category_df = category_df.rename(columns={selected_category: "Daily Total"})
else:
    category_df = filtered_df[["Date", "Daily Total"]].copy()


# The below three lines code is for calculating the Month on Month expense change. To make the code clean I am putting it here. 
monthly_spent = df.groupby('Month', sort=False)['Daily Total'].sum()
mom_change = monthly_spent.pct_change() * 100 
latest_mom_change = mom_change.iloc[-1] 

#Here I am using st.columns to display the five metrices I made across each other. 

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_spending = category_df["Daily Total"].sum()
    st.metric(label="Total Spending", value=f"₹{total_spending:,.2f}")

with col2:
    avg_daily_spending = category_df["Daily Total"].mean()
    st.metric(label="Avg Daily Spending", value=f"₹{avg_daily_spending:,.2f}")

with col3:
    max_spending = category_df["Daily Total"].max()
    st.metric(label="Highest Spending", value=f"₹{max_spending:,.2f}")

with col4:
    income_value = filtered_df["Income"].sum()
    st.metric(label="Total Income", value=f"₹{income_value:,.2f}")
with col5:
    st.metric(label="MOM expense Change", value=f"{latest_mom_change:,.2f}%")

#After the metrices I am going to display the line plot of my net expenses of each day I spent any money.
# This dynamically gets changed according to the category

#st.subheader("Daily Spending Trend") I don't want subheading so I have commented this line.
fig = px.line(category_df, x="Date", y="Daily Total", title="Spending Trend", markers=True)
st.plotly_chart(fig, use_container_width=True)

# I am plotting two graphs across each other so I will again use st.columns
c1, c2 = st.columns(2)
with c1:
    # Filter based on selected category and month
    if selected_category == "All Categories":
        df_to_plot = df[df['Month'] == selected_month] if selected_month != "All" else df
        df_to_plot = df_to_plot[["Date", "Day", "Daily Total"]].copy()
        y_label = "Daily Total"
    else:
        df_to_plot = df[df['Month'] == selected_month] if selected_month != "All" else df
        df_to_plot = df_to_plot[["Date", "Day", selected_category]].rename(columns={selected_category: "Daily Total"})

    # Group by Day
    df_to_plot = df_to_plot.groupby("Day", as_index=False).agg({"Daily Total": "sum"})

    # Capture unique day order from user's CSV
    original_day_order = df[df['Month'] == selected_month]['Day'].drop_duplicates().tolist() if selected_month != "All" else df['Day'].drop_duplicates().tolist()

    # Apply the order to the grouped DataFrame
    df_to_plot['Day'] = pd.Categorical(df_to_plot['Day'], categories=original_day_order, ordered=True)
    df_to_plot = df_to_plot.sort_values('Day')

    # Caption for filter summary
    filter_summary = f"Month: **{selected_month}** | Category: **{selected_category}**"
    st.caption(f"Showing spending filtered by → {filter_summary}")

    # Plot the bar chart
    fig2 = px.bar(
        df_to_plot,
        x='Day',
        y='Daily Total',
        title="The Heavy Expense Day",
        color_discrete_sequence=['#1f77b4']
    )

    st.plotly_chart(fig2, use_container_width=True)




#plotting the second graph for monthly comparisons to see if I overspent or underspent.
with c2:
    # st.subheader("Month-on-Month Spending Change")
    mom_change_df = mom_change.reset_index().dropna()
    mom_change_df.columns = ['Month', 'Percentage Change']

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=mom_change_df['Month'],
        y=mom_change_df['Percentage Change'],
        marker_color=['green' if x > 0 else '#1f77b4' for x in mom_change_df['Percentage Change']],
        text=mom_change_df['Percentage Change'].apply(lambda x: f"{x:.2f}%"),
        textposition='outside'
    ))

    fig3.update_layout(
        title="Hoping for more Blues(underspent compared to last month)",
        xaxis_title="Month",
        yaxis_title="Percentage Change (%)",
        xaxis=dict(categoryorder="array", categoryarray=mom_change_df['Month']),
        yaxis=dict(showgrid=True),
        showlegend=False
    )
    st.plotly_chart(fig3, use_container_width=True)


#Plotting a Bar Gragh for identfying the most spent categories.
#st.subheader("Category wise Monthly Spending")
# Filter for selected month and category
# Extract months in the order they appear in the user's data
ordered_months = df['Month'].drop_duplicates().tolist()
category_monthly = filtered_df.groupby('Month')[category_cols].sum().reset_index()
category_monthly['Month'] = pd.Categorical(category_monthly['Month'], categories=ordered_months, 
ordered=True)
category_monthly = category_monthly.sort_values('Month')

fig4 = px.bar(
    category_monthly,
    x='Month',
    y=category_cols,
    title="Who is the Culprit?",
    labels={'value': "Amount (₹)", 'Month': "Month"},
    barmode="stack",
    text_auto=True,
)

st.plotly_chart(fig4, use_container_width=True)


#Again, Plotting a Bar Graph for identifying which month I spent more money and the average of expense.
# st.subheader("Monthly Spending Comparison")

monthly_spent = df.groupby('Month', sort=False)['Daily Total'].sum().reset_index()
avg_spent = monthly_spent['Daily Total'].mean()

fig5 = px.bar(
    monthly_spent,
    x='Month',
    y='Daily Total',
    title="The expense heavy month...",
    labels={'Daily Total': "Total Spend (₹)", 'Month': "Month"},
    text_auto=True,
    color_discrete_sequence=[px.colors.qualitative.Set2[0]]
)
fig5.add_hline(
    y=avg_spent,
    line_dash="dash",
    line_color="red",
    name=f"Average Spend (₹{avg_spent:,.0f})" 
)

fig5.add_trace(go.Scatter(
    x=[None], y=[None],
    mode='lines',
    name=f"Average Spend (₹{avg_spent:,.0f})",
    line=dict(color='red', dash='dash')
))

st.plotly_chart(fig5, use_container_width=True)


#Setting up a expense limit for next month based on the median of all the months.
last_date = df['Date'].max()
last_month = last_date.strftime('%B')
last_year = last_date.year

if last_date.month == 12:  # If December, next month is January of next year
    next_month = 'January'
    next_year = last_year + 1
else:
    next_month = (last_date + timedelta(days=31)).strftime('%B')  
    next_year = last_year 

recommended_limit = monthly_spent['Daily Total'].median()
st.subheader(f"Recommended Expense Limit for {next_month} {next_year}")
st.markdown(f"**Based on past spending, The recommended monthly limit for {next_month} is:**")
st.markdown(f"### ₹{recommended_limit:,.2f}")

st.markdown("---")
st.markdown(
    "<center>Made with logic by Student for Students• Powered by Streamlit + Plotly</center>",
    unsafe_allow_html=True
)
