import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime

st.set_page_config(page_title="Defect Tracking Dashboard", layout="wide")

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'defect_data' not in st.session_state:
    st.session_state.defect_data = []


# Admin credentials stored in JSON
def load_credentials():
    if os.path.exists('admin_credentials.json'):
        with open('admin_credentials.json', 'r') as f:
            return json.load(f)
    return {"username": "admin", "password": "admin123"}


def save_credentials(credentials):
    with open('admin_credentials.json', 'w') as f:
        json.dump(credentials, f)


def load_data():
    try:
        if os.path.exists('defect_data.json'):
            with open('defect_data.json', 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return []


def save_data(data):
    with open('defect_data.json', 'w') as f:
        json.dump(data, f)


def create_defect_charts(df):
    fig_platform = px.bar(df.groupby('Platform')['Count'].sum().reset_index(),
                          x='Platform', y='Count', title='Defects by Platform')

    fig_priority = px.pie(df.groupby('Priority')['Count'].sum().reset_index(),
                          values='Count', names='Priority', title='Defects by Priority')

    fig_trend = px.line(df.groupby(['Release', 'Platform'])['Count'].sum().reset_index(),
                        x='Release', y='Count', color='Platform', title='Defect Trend Across Releases')

    return fig_platform, fig_priority, fig_trend


def show_dashboard():
    if st.session_state.defect_data:
        df = pd.DataFrame(st.session_state.defect_data)
        fig_platform, fig_priority, fig_trend = create_defect_charts(df)

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_platform, use_container_width=True)
        with col2:
            st.plotly_chart(fig_priority, use_container_width=True)

        st.plotly_chart(fig_trend, use_container_width=True)
        st.dataframe(df)
    else:
        st.info("No data available.")


def show_defect_form():
    col1, col2, col3 = st.columns(3)

    with col1:
        release = st.text_input("Release Version", placeholder="e.g., v1.0.0")
        platform = st.selectbox("Platform", ["Web", "Android", "iOS"])
        component = st.text_input("Component")

    with col2:
        date = st.date_input("Date")
        priority = st.selectbox("Priority", ["Critical", "High", "Medium", "Low"])
        severity = st.selectbox("Severity", ["Blocker", "Major", "Minor", "Trivial"])

    with col3:
        count = st.number_input("Number of Defects", min_value=0, value=0)
        status = st.selectbox("Status", ["Open", "In Progress", "Fixed", "Closed"])
        assigned_to = st.text_input("Assigned To")

    description = st.text_area("Description")

    if st.button("Add Defect"):
        new_entry = {
            "Release": release,
            "Platform": platform,
            "Component": component,
            "Date": date.strftime("%Y-%m-%d"),
            "Priority": priority,
            "Severity": severity,
            "Count": count,
            "Status": status,
            "AssignedTo": assigned_to,
            "Description": description
        }
        st.session_state.defect_data.append(new_entry)
        save_data(st.session_state.defect_data)
        st.success("Data added successfully!")


def show_manage_data():
    df = pd.DataFrame(st.session_state.defect_data)
    if not df.empty:
        edited_df = st.data_editor(df)
        if st.button("Save Changes"):
            st.session_state.defect_data = edited_df.to_dict('records')
            save_data(st.session_state.defect_data)
            st.success("Changes saved successfully!")


def show_settings():
    st.subheader("Change Admin Password")
    credentials = load_credentials()
    current_password = st.text_input("Current Password", type="password")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")

    if st.button("Change Password"):
        if current_password == credentials["password"]:
            if new_password == confirm_password:
                credentials["password"] = new_password
                save_credentials(credentials)
                st.success("Password changed successfully!")
            else:
                st.error("New passwords don't match!")
        else:
            st.error("Current password is incorrect!")


def main():
    st.title("🪲 Defect Tracking Dashboard")
    credentials = load_credentials()
    st.session_state.defect_data = load_data()

    # Admin login sidebar
    with st.sidebar:
        if not st.session_state.authenticated:
            st.header("Admin Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.button("Login"):
                if username == credentials["username"] and password == credentials["password"]:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        else:
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.rerun()

    if st.session_state.authenticated:
        tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Add Defects", "Manage Data", "Settings"])

        with tab1:
            show_dashboard()
        with tab2:
            show_defect_form()
        with tab3:
            show_manage_data()
        with tab4:
            show_settings()
    else:
        show_dashboard()


if __name__ == "__main__":
    main()
