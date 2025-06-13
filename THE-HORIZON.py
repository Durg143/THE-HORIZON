# 📚 Streamlit Book Publishing App with Login, Reviews, and Likes

import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from streamlit_authenticator import Authenticate
import pandas as pd
import datetime

# -------------- CONFIGURATION (replace with secure methods in production) --------------

st.set_page_config(page_title="My Book App", layout="wide")
st.markdown("""
    <style>
        .main { background-color: #0e1117; color: white; }
        .stButton>button { color: white; background-color: #5c5cfa; }
    </style>
""", unsafe_allow_html=True)

# Fake database (in production, use Firebase, Supabase, or MongoDB)
if 'reviews' not in st.session_state:
    st.session_state.reviews = []
if 'likes' not in st.session_state:
    st.session_state.likes = {}

# -------------- LOGIN PAGE --------------

st.sidebar.title("Welcome to BookWorld")
st.sidebar.markdown("Login to continue")

login_method = st.sidebar.radio("Login Method", ["Continue with Google", "Continue with X (Twitter)"])

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")
login_button = st.sidebar.button("Login")

if login_button:
    if username and password:
        st.session_state.logged_in = True
        st.session_state.user = username
        st.experimental_rerun()
    else:
        st.sidebar.error("Please enter login details")

# -------------- MAIN APP INTERFACE --------------
if 'logged_in' in st.session_state and st.session_state.logged_in:
    st.title(f"📘 Welcome, {st.session_state.user}")
    st.header("My Book: The Adventure Begins")

    st.markdown("### Chapters")
    chapters = {
        "Chapter 1: The Call to Adventure": "Once upon a time...",
        "Chapter 2: Into the Unknown": "The hero steps out...",
        "Chapter 3: Triumph & Trials": "Challenges arise..."
    }

    for chapter, content in chapters.items():
        with st.expander(chapter):
            st.markdown(content)
            
            # Like Button
            like_key = f"like_{chapter}"
            if like_key not in st.session_state.likes:
                st.session_state.likes[like_key] = 0
            
            if st.button("👍 Like", key=like_key):
                st.session_state.likes[like_key] += 1
            st.write(f"{st.session_state.likes[like_key]} likes")

            # Review Input
            with st.form(key=f"review_form_{chapter}"):
                review = st.text_area("Leave a review")
                submit_review = st.form_submit_button("Submit")
                if submit_review and review:
                    st.session_state.reviews.append({
                        "chapter": chapter,
                        "user": st.session_state.user,
                        "review": review,
                        "timestamp": datetime.datetime.now()
                    })

            # Display Reviews
            for r in st.session_state.reviews:
                if r['chapter'] == chapter:
                    st.markdown(f"**{r['user']}** ({r['timestamp'].strftime('%Y-%m-%d %H:%M')}): {r['review']}")

# -------------- HOW TO MAKE IT OFFICIAL --------------

# To turn this into an official app:
# 1. Replace fake login with Firebase Auth or Auth0 integration.
# 2. Store likes/reviews using a real database: Firebase, Supabase, MongoDB Atlas.
# 3. Host the app on Streamlit Community Cloud or deploy via Docker on services like Heroku or Render.
# 4. Buy a domain and link it via reverse proxy if needed.
# 5. Add Terms of Service, Privacy Policy, and secure login flow for user data protection.

# Optional Libraries to Add:
# - streamlit_authenticator
# - firebase_admin
# - pymongo / supabase-py
# - streamlit_extras for better UX
