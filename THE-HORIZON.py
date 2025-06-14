import streamlit as st
from pymongo import MongoClient
import bcrypt
from datetime import datetime
import PyPDF2

# ---------------------- 🌐 MongoDB Setup ----------------------
MONGO_URL = st.secrets["mongo"]["url"]
client = MongoClient(MONGO_URL)
db = client["book_platform"]
users_col = db["users"]
chapters_col = db["chapters"]
reviews_col = db["reviews"]
likes_col = db["likes"]

# ---------------------- 🔑 Auth Helpers ----------------------
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)

# ---------------------- 🌐 Session Init ----------------------
if "email" not in st.session_state:
    st.session_state.email = None

# ---------------------- 🧾 App Title ----------------------
st.set_page_config(page_title="Book Platform", page_icon="📚", layout="centered")
st.title("📚 Book Publishing Platform")

# ---------------------- 🔐 Login & Signup ----------------------
if not st.session_state.email:
    tabs = st.tabs(["🔑 Login", "📝 Sign Up"])

    with tabs[0]:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            user = users_col.find_one({"email": email})
            if user and check_password(password, user["password"]):
                st.session_state.email = email
                st.success("Welcome back!")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tabs[1]:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_pass")
        if st.button("Sign Up"):
            if users_col.find_one({"email": email}):
                st.warning("Email already registered.")
            else:
                hashed = hash_password(password)
                users_col.insert_one({"email": email, "password": hashed})
                st.success("User registered. Please log in.")

# ---------------------- ✍️ Logged In ----------------------
else:
    st.success(f"🎉 Logged in as: {st.session_state.email}")
    email = st.session_state.email
    is_admin = email == "pp26012006@gmail.com"

    if is_admin:
        with st.expander("📤 Upload Chapter"):
            uploaded_file = st.file_uploader("Upload chapter (Text or PDF)", type=["txt", "pdf"])
            chapter_id = st.text_input("Chapter ID")
            chapter_title = st.text_input("Chapter Title")

            if uploaded_file and chapter_title and chapter_id:
                content = ""
                if uploaded_file.type == "application/pdf":
                    reader = PyPDF2.PdfReader(uploaded_file)
                    content = "\n".join([page.extract_text() for page in reader.pages])
                else:
                    content = uploaded_file.read().decode("utf-8")

                if chapters_col.find_one({"chapter_id": chapter_id}):
                    st.error("Chapter ID already exists.")
                else:
                    chapters_col.insert_one({
                        "chapter_id": chapter_id,
                        "title": chapter_title,
                        "content": content,
                        "uploaded_by": email,
                        "timestamp": datetime.utcnow()
                    })
                    st.success("✅ Chapter uploaded!")

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
            likes_col.update_one(
                {"chapter_id": selected_ch['chapter_id']},
                {"$addToSet": {"liked_by": email}},
                upsert=True
            )
            st.success("❤️ Liked!")

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

    if st.button("Logout"):
        st.session_state.email = None
        st.experimental_rerun()

# ---------------------- 📌 Footer ----------------------
with st.expander("Privacy Policy"):
    st.markdown("""
    - We respect your privacy.
    - Your data is securely stored in our cloud database.
    - We do not sell or misuse your information.
    - For any queries, contact: **pp26012006@gmail.com**
    """)

st.markdown("---")
st.markdown("durg143 Book Publishing Platform | All Rights Reserved", unsafe_allow_html=True)

with st.expander("📘 About the Author"):
    st.markdown("""
    Myself Durga Prasad Potnuru, a passionate storyteller and author.

    I believe in the power of words to heal, inspire, and ignite the imagination.  
    My books often explore emotional resilience, connection, and the horizon between dreams and reality.

    You can follow my journey on [Instagram](https://www.instagram.com/mr_bluff_143/) or [Twitter](https://x.com/durgaprasad069).
    or [Linkedin](https://www.linkedin.com/in/durga-prasad-potnuru-a60779293/)
    """)

with st.expander("📬 Contact Us"):
    st.markdown("""
    - 📧 **Email**: pp26012006@gmail.com  
    - 📱 **Instagram**: [@mr_bluff_143](https://www.instagram.com/mr_bluff_143/)
    """)

