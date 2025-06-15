import streamlit as st
import datetime
import pymongo
import base64

# -------------------- MongoDB Setup --------------------
client = pymongo.MongoClient("mongodb+srv://<your_connection_string>")
db = client["horizon"]
users_col = db["users"]
likes_col = db["likes"]

# -------------------- Background Setup --------------------
def set_bg_image(image_path):
    with open(image_path, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode()
    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{encoded_string}");
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
        background-attachment: fixed;
        transition: background 0.5s ease-in-out;
    }}
    .block-container {{
        background-color: rgba(0, 0, 0, 0.6);
        padding: 2rem;
        border-radius: 10px;
        animation: fadein 2s ease-in;
    }}
    @keyframes fadein {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# -------------------- Authentication --------------------
def login():
    st.subheader("🔐 Login / Signup")
    email = st.text_input("Email")
    mobile = st.text_input("Mobile Number")
    name = st.text_input("Your Name")
    if st.button("Login"):
        existing_user = users_col.find_one({"email": email})
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if existing_user:
            st.warning("⚠️ This email is already registered. Logging in...")
            users_col.update_one({"email": email}, {"$push": {"logins": now}})
        else:
            users_col.insert_one({
                "email": email,
                "mobile": mobile,
                "name": name,
                "logins": [now]
            })
            st.success("✅ Account created and logged in!")
        st.session_state["user"] = email
        st.session_state["name"] = name
        st.session_state["mobile"] = mobile
        st.rerun()

# -------------------- Sidebar User Info --------------------
def show_sidebar_info():
    st.sidebar.markdown("### 👤 Logged in as:")
    st.sidebar.markdown(f"**{st.session_state.get('name', 'N/A')}**")
    st.sidebar.markdown(f"📧 {st.session_state.get('user', 'N/A')}")
    st.sidebar.markdown(f"📱 {st.session_state.get('mobile', 'N/A')}")
    st.sidebar.markdown("---")
    st.sidebar.markdown("✅ Mobile numbers and emails are stored securely.")
    st.sidebar.markdown("🔁 One email cannot be used to sign up again.")

# -------------------- Display Registered Users --------------------
def show_all_users():
    st.subheader("👥 All Registered Users")
    all_users = users_col.find()
    for u in all_users:
        name = u.get("name", "N/A")
        email = u.get("email", "N/A")
        mobile = u.get("mobile", "N/A")
        last_login = u.get("logins", ["N/A"])[-1]
        st.markdown(f"""**{name}**  
📧 {email}  
📱 {mobile}  
🕒 Last Login: {last_login}  
---""")

# -------------------- Show Book Chapters --------------------
def show_book():
    st.title("📘 THE HORIZON - A Small Story")
    chapters = {
        "Chapter 1: The Beginning": "This is the story of a distant horizon...",
        "Chapter 2: The Journey": "Through trials and change, they walked together...",
        "Chapter 3: The Truth": "Secrets are revealed as paths split and converge...",
    }
    for chapter, content in chapters.items():
        with st.expander(chapter, expanded=False):
            st.write(content)
            if st.button(f"❤️ Like", key=chapter):
                likes_col.insert_one({
                    "user": st.session_state["user"],
                    "chapter": chapter,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.success("Thanks for liking!")

# -------------------- Admin Panel --------------------
def show_admin_panel():
    st.subheader("📊 Admin Panel - Likes Data")
    data = likes_col.find()
    for entry in data:
        user = entry.get("user", "N/A")
        chapter = entry.get("chapter", "N/A")
        time = entry.get("timestamp", "N/A")
        st.markdown(f"📌 **{user}** liked **{chapter}** at 🕒 {time}")

# -------------------- Main UI --------------------
def main():
    set_bg_image("background.jpg",width=100)
    st.sidebar.image("dp_logo.png", width=100)
    st.sidebar.title("📚 THE HORIZON")
    if "user" in st.session_state:
        show_sidebar_info()

    menu = ["Login", "Read Book", "Users", "Admin"]
    choice = st.sidebar.radio("Navigate", menu)

    if "user" not in st.session_state:
        login()
    elif choice == "Read Book":
        show_book()
    elif choice == "Users":
        show_all_users()
    elif choice == "Admin":
        show_admin_panel()
    else:
        login()

if __name__ == "__main__":
    main()
