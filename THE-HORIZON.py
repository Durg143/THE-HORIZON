import streamlit as st
from pymongo import MongoClient
import bcrypt
import datetime

# ----------------------  MongoDB Configuration ----------------------
MONGO_URL = mongodb+srv://pp26012006:<db_password>@the-horizon.xp1c3zz.mongodb.net/?retryWrites=true&w=majority&appName=THE-HORIZON  # 🔧 Your Mongo URI
client = MongoClient(MONGO_URL)
db = client["book_platform"]
users_col = db["users"]
chapters_col = db["chapters"]
reviews_col = db["reviews"]
likes_col = db["likes"]

st.set_page_config(page_title="Book Publisher", layout="wide")

# ---------------------- AUTH ----------------------
def create_user(email, password):
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    users_col.insert_one({"email": email, "password": hashed_pw})

def authenticate_user(email, password):
    user = users_col.find_one({"email": email})
    if user and bcrypt.checkpw(password.encode(), user["password"]):
        return user
    return None

# ---------------------- SESSION ----------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = None

if not st.session_state.logged_in:
    st.title("📚 Login to Book Platform")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate_user(email, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user_email = user["email"]
            st.success("✅ Logged in successfully!")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid credentials")

    if st.button("Sign Up"):
        if users_col.find_one({"email": email}):
            st.warning("User already exists!")
        else:
            create_user(email, password)
            st.success("✅ Account created! You can now log in.")

# ---------------------- MAIN APP ----------------------
if st.session_state.logged_in:
    email = st.session_state.user_email
    is_admin = email == "admin@example.com"  # 🔧 CHANGE TO YOUR ADMIN EMAIL

    st.sidebar.title(f"👋 Welcome, {email.split('@')[0]}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.experimental_rerun()

    st.title("📖 My Book Platform")

    # ---------------------- ADMIN: Upload New Chapter ----------------------
    if is_admin:
        st.markdown("## ✍️ Upload New Chapter (Admin Only)")
        with st.form("upload_form"):
            chapter_id = st.text_input("Chapter ID (e.g., chapter1)")
            chapter_title = st.text_input("Chapter Title")
            chapter_content = st.text_area("Chapter Content")
            submitted = st.form_submit_button("Upload Chapter")
            if submitted:
                if chapter_id and chapter_title and chapter_content:
                    chapters_col.update_one(
                        {"chapter_id": chapter_id},
                        {"$set": {
                            "chapter_id": chapter_id,
                            "title": chapter_title,
                            "content": chapter_content,
                            "uploaded_by": email,
                            "timestamp": datetime.datetime.now()
                        }},
                        upsert=True
                    )
                    st.success("✅ Chapter uploaded!")
                else:
                    st.error("❌ All fields are required.")

    # ---------------------- Reader View ----------------------
    st.markdown("## 📚 Read and Review Chapters")
    chapter_list = list(chapters_col.find())
    chapter_titles = [f"{c['chapter_id']} - {c['title']}" for c in chapter_list]

    if chapter_list:
        selected = st.selectbox("Select a Chapter", chapter_titles)
        selected_chapter = chapter_list[chapter_titles.index(selected)]

        st.subheader(selected_chapter["title"])
        st.write(selected_chapter["content"])

        # ---------------------- Likes ----------------------
        like_entry = likes_col.find_one({"chapter_id": selected_chapter["chapter_id"]})
        liked_by = like_entry["liked_by"] if like_entry else []
        likes_count = len(liked_by)
        has_liked = email in liked_by

        if not has_liked:
            if st.button("👍 Like"):
                likes_col.update_one(
                    {"chapter_id": selected_chapter["chapter_id"]},
                    {"$addToSet": {"liked_by": email}},
                    upsert=True
                )
                st.experimental_rerun()

        st.write(f"👍 {likes_count} Likes")

        # ---------------------- Reviews ----------------------
        st.markdown("### 💬 Leave a Review")
        review_text = st.text_area("Your Review")
        if st.button("Submit Review"):
            reviews_col.insert_one({
                "chapter_id": selected_chapter["chapter_id"],
                "email": email,
                "text": review_text,
                "timestamp": datetime.datetime.now()
            })
            st.success("✅ Review submitted!")

        st.markdown("### 📝 Reader Reviews")
        all_reviews = list(reviews_col.find({"chapter_id": selected_chapter["chapter_id"]}))
        for r in all_reviews:
            st.info(f"**{r['email']}** at *{r['timestamp'].strftime('%Y-%m-%d %H:%M')}*:\n\n{r['text']}")
    else:
        st.info("No chapters published yet.")

# Optional Libraries to Add:
# - streamlit_authenticator
# - firebase_admin
# - pymongo / supabase-py
# - streamlit_extras for better UX
