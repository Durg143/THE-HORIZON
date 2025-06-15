import streamlit as st
import base64
from pymongo import MongoClient
from datetime import datetime
import uuid

# MongoDB setup
client = MongoClient("your_mongodb_connection_string")
db = client["the_horizon"]
users_col = db["users"]
likes_col = db["likes"]
logins_col = db["logins"]

# ---------- UI Enhancements ----------
def set_bg_image(image_path):
    with open(image_path, "rb") as img:
        base64_img = base64.b64encode(img.read()).decode()
    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{base64_img}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        animation: fadeIn 2s ease-in-out;
    }}

    @keyframes fadeIn {{
        0% {{ opacity: 0; transform: translateY(-10px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
    }}

    .title {{
        font-size: 50px; 
        font-weight: bold; 
        text-align: center; 
        color: white; 
        animation: fadeIn 2s ease-in-out;
    }}

    .subtitle {{
        font-size: 24px; 
        text-align: center; 
        color: lightgray;
        animation: fadeIn 3s ease-in-out;
    }}

    .content-box {{
        background-color: rgba(0, 0, 0, 0.5); 
        padding: 20px; 
        border-radius: 10px; 
        margin-top: 20px;
        animation: fadeIn 2s ease-in-out;
    }}

    button[kind="primary"] {{
        transition: all 0.3s ease-in-out;
    }}

    button[kind="primary"]:hover {{
        transform: scale(1.05);
        background-color: #ff4b4b !important;
        color: white !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Set background
set_bg_image("background.jpg")

# Title
st.markdown('<div class="title">THE HORIZON</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">A Small Story</div>', unsafe_allow_html=True)

# Sidebar Login/Signup
st.sidebar.header("Login / Signup")
menu = st.sidebar.selectbox("Choose an option", ["Signup", "Login", "Admin Panel"])

# ---------- Signup ----------
if menu == "Signup":
    name = st.sidebar.text_input("Full Name")
    email = st.sidebar.text_input("Email")
    mobile = st.sidebar.text_input("Mobile Number")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Create Account"):
        if users_col.find_one({"email": email}):
            st.sidebar.error("Email already exists.")
        else:
            users_col.insert_one({
                "_id": str(uuid.uuid4()),
                "name": name,
                "email": email,
                "mobile": mobile,
                "password": password
            })
            st.sidebar.success("Account created successfully!")

# ---------- Login ----------
elif menu == "Login":
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        user = users_col.find_one({"email": email, "password": password})
        if user:
            st.session_state.user = user
            st.success(f"Welcome {user['name']}!")

            # Track login
            logins_col.insert_one({
                "user_id": user["_id"],
                "email": user["email"],
                "timestamp": datetime.now()
            })

            # Chapter Content
            st.markdown('<div class="content-box">', unsafe_allow_html=True)
            st.header("Chapter 1: The Beginning")
            st.write("In a world divided by chaos and silence, two souls found a way to echo through the storm...")
            if st.button("❤️ Like this chapter"):
                if not likes_col.find_one({"user_id": user["_id"], "chapter": "chapter1"}):
                    likes_col.insert_one({
                        "user_id": user["_id"],
                        "email": user["email"],
                        "chapter": "chapter1",
                        "liked_at": datetime.now()
                    })
                    st.success("Thanks for liking!")
                else:
                    st.info("You’ve already liked this chapter.")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.sidebar.error("Invalid credentials.")

# ---------- Admin Panel ----------
elif menu == "Admin Panel":
    st.markdown('<div class="content-box">', unsafe_allow_html=True)
    st.subheader("👥 Registered Users")
    users = list(users_col.find())
    for u in users:
        st.markdown(f"- **{u['name']}** ({u['email']}, {u['mobile']})")

    st.subheader("📅 Login History")
    logins = list(logins_col.find().sort("timestamp", -1))
    for l in logins:
        st.markdown(f"- {l['email']} at `{l['timestamp']}`")

    st.subheader("👍 Likes on Chapters")
    likes = list(likes_col.find())
    for like in likes:
       st.markdown(
    f"**{u.get('name', 'N/A')}** | 📧 {u.get('email', 'N/A')} | 📱 {u.get('mobile', 'N/A')} | ⏱️ Last Login: {u.get('last_login', 'N/A')}"
)

    st.markdown('</div>', unsafe_allow_html=True)
