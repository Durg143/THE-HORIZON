# streamlit_app.py
import streamlit as st
from pymongo import MongoClient
import bcrypt
from datetime import datetime
from PIL import Image
import base64

# ---------------------- 🌄 Background and Logo ----------------------

def set_bg_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    page_bg_img = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded_string}");
        background-size: contain;
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
        background-attachment: fixed;
        transition: background 0.5s ease-in-out;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

set_bg_image("background.jpg")  # 🔧 Place your background.jpg in the same directory
st.image("logo.png", width=200)  # 🔧 Place your logo.png in the same directory

# ---------------------- 🔐 MongoDB Connection ----------------------
MONGO_URL = st.secrets["mongo"]["url"]
client = MongoClient(MONGO_URL)
db = client["book_platform"]
users_col = db["users"]
chapters_col = db["chapters"]
reviews_col = db["reviews"]
likes_col = db["likes"]

# ---------------------- 🔑 Authentication ----------------------
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)

# ---------------------- 📌 Session State ----------------------
if "email" not in st.session_state:
    st.session_state.email = None

# ---------------------- 🔐 Login / Sign Up ----------------------
st.title("📚 THE HORIZON - Book Publishing Platform")

if not st.session_state.email:
    auth_tab = st.tabs(["🔑 Login", "📝 Sign Up"])

    with auth_tab[0]:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            user = users_col.find_one({"email": email})
            if user and check_password(password, user["password"]):
                st.session_state.email = email
                users_col.update_one({"email": email}, {"$set": {"last_login": datetime.utcnow()}})
                st.success("Welcome back!")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with auth_tab[1]:
        name = st.text_input("Full Name")
        mobile = st.text_input("Mobile Number")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Sign Up"):
            if users_col.find_one({"email": email}):
                st.warning("Email already registered.")
            else:
                hashed = hash_password(password)
                users_col.insert_one({
                    "name": name,
                    "mobile": mobile,
                    "email": email,
                    "password": hashed,
                    "created_at": datetime.utcnow(),
                    "last_login": datetime.utcnow()
                })
                st.success("User registered. Please log in.")

else:
    st.success(f"🎉 Logged in as: {st.session_state.email}")
    email = st.session_state.email
    user = users_col.find_one({"email": email})
    is_admin = email == "pp26012006@gmail.com"

    # ---------------------- ✍️ Upload Chapter (Admin) ----------------------
    if is_admin:
        st.markdown("## ✍️ Upload New Chapter")
        with st.form("upload_form"):
            chapter_id = st.text_input("Chapter ID")
            chapter_title = st.text_input("Chapter Title")
            chapter_content = st.text_area("Chapter Content")
            submitted = st.form_submit_button("Upload Chapter")
            if submitted:
                if chapters_col.find_one({"chapter_id": chapter_id}):
                    st.error("Chapter ID already exists.")
                else:
                    chapters_col.insert_one({
                        "chapter_id": chapter_id,
                        "title": chapter_title,
                        "content": chapter_content,
                        "uploaded_by": email,
                        "timestamp": datetime.utcnow()
                    })
                    st.success("✅ Chapter uploaded!")

    # ---------------------- 📋 Manage Chapters (Admin) ----------------------
    if is_admin:
        st.markdown("## 📋 Manage Uploaded Chapters")
        all_chapters = list(chapters_col.find())

        for ch in all_chapters:
            with st.expander(f"{ch['chapter_id']} — {ch['title']}"):
                new_title = st.text_input("Edit Title", value=ch['title'], key=f"title_{ch['chapter_id']}")
                new_content = st.text_area("Edit Content", value=ch['content'], key=f"content_{ch['chapter_id']}")
                if st.button("✏️ Save Changes", key=f"save_{ch['chapter_id']}"):
                    chapters_col.update_one({"chapter_id": ch['chapter_id']}, {"$set": {"title": new_title, "content": new_content}})
                    st.success("✅ Chapter updated.")
                    st.experimental_rerun()

                if st.button("🗑️ Delete Chapter", key=f"delete_{ch['chapter_id']}"):
                    chapters_col.delete_one({"chapter_id": ch['chapter_id']})
                    reviews_col.delete_many({"chapter_id": ch['chapter_id']})
                    likes_col.delete_many({"chapter_id": ch['chapter_id']})
                    st.warning("🗑️ Chapter deleted.")
                    st.experimental_rerun()

    # ---------------------- 📖 Read & Review Chapters ----------------------
    st.markdown("## 📖 Read and Review Chapters")
    chapter_titles = [f"{c['chapter_id']} — {c['title']}" for c in chapters_col.find()]
    chapter_map = {f"{c['chapter_id']} — {c['title']}": c for c in chapters_col.find()}

    if chapter_titles:
        selected = st.selectbox("Select a Chapter", chapter_titles)
        selected_ch = chapter_map[selected]

        st.subheader(selected_ch['title'])
        st.write(selected_ch['content'])

        like_doc = likes_col.find_one({"chapter_id": selected_ch['chapter_id']}) or {"liked_by": []}
        has_liked = email in like_doc["liked_by"]

        if not has_liked and st.button("❤️ Like"):
            likes_col.update_one({"chapter_id": selected_ch['chapter_id']}, {"$addToSet": {"liked_by": email}}, upsert=True)
            st.success("❤️ Liked!")

        if is_admin:
            st.markdown(f"**Liked by:** {', '.join(like_doc['liked_by'])}")

        st.markdown(f"**Total Likes:** {len(like_doc['liked_by']) if like_doc else 0}")

        st.subheader("💬 Leave a Review")
        review_text = st.text_area("Your Review")
        if st.button("Submit Review"):
            reviews_col.insert_one({
                "chapter_id": selected_ch['chapter_id'],
                "email": email,
                "text": review_text,
                "timestamp": datetime.utcnow()
            })
            st.success("✅ Review submitted!")

        st.subheader("📝 Reader Reviews")
        all_reviews = reviews_col.find({"chapter_id": selected_ch['chapter_id']}).sort("timestamp", -1)
        for r in all_reviews:
            st.markdown(f"**{r['email']}**: {r['text']}")
    else:
        st.info("No chapters uploaded yet.")

    # ---------------------- 👁️ Admin: User View ----------------------
    if is_admin:
        st.markdown("## 👥 All Registered Users")
        users = users_col.find()
        for u in users:
           st.markdown(
    f"**{u.get('name', 'N/A')}** | 📧 {u.get('email', 'N/A')} | 📱 {u.get('mobile', 'N/A')} | ⏱️ Last Login: {u.get('last_login', 'N/A')}"
)

    if st.button("Logout"):
        st.session_state.email = None
        st.rerun()

# ---------------------------- 📜 Footer & Policy ----------------------------
with st.expander("Privacy Policy"):
    st.markdown("""
    - We respect your privacy.
    - Your data is securely stored in our cloud database.
    - We do not sell or misuse your information.
    - For any queries, contact: **pp26012006@gmail.com**
    """)

with st.expander("📘 About the Author"):
    st.markdown("""
    Myself Durga Prasad Potnuru, a passionate storyteller and author.
    I believe in the power of words to heal, inspire, and ignite imagination.
    Connect on [Instagram](https://www.instagram.com/mr_bluff_143/) | [Twitter](https://x.com/durgaprasad069) | [Linkedin](https://www.linkedin.com/in/durga-prasad-potnuru-a60779293/)
    """)

with st.expander("📬 Contact Us"):
    st.markdown("""
    - 📧 **Email**: pp26012006@gmail.com
    - 📱 **Instagram**: [@mr_bluff_143](https://www.instagram.com/mr_bluff_143/)
    """)

st.markdown("---")
st.markdown("<center><b>THE HORIZON</b> Book Publishing Platform | All Rights Reserved</center>", unsafe_allow_html=True)
