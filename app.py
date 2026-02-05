import streamlit as st
import requests
import google.generativeai as genai
from datetime import datetime

# Configuration
st.set_page_config(
    page_title="Hardcover AI (Dracula Edition)", 
    page_icon="🧛", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Credentials
def get_credentials():
    hc_token = st.secrets.get("connections", {}).get("hardcover_token", "")
    gem_key = st.secrets.get("connections", {}).get("gemini_key", "")
    
    if not hc_token or not gem_key:
        with st.sidebar.expander("🔐 API Credentials", expanded=True):
            st.caption("Secrets not found. Enter manually.")
            if not hc_token: hc_token = st.text_input("Hardcover Token", type="password")
            if not gem_key: gem_key = st.text_input("Gemini API Key", type="password")
    return hc_token, gem_key

# API client
def fetch_enhanced_library(token):
    url = "https://api.hardcover.app/v1/graphql"
    headers = {"authorization": token, "content-type": "application/json"}
    
    query = """
    query GetEnhancedLibrary {
      me {
        user_books(
          where: { status_id: { _eq: 3 } } 
          limit: 1000
          order_by: { updated_at: desc }
        ) {
          rating
          book {
            title
            release_date
            contributions { author { name } }
          }
        }
      }
    }
    """
    try:
        response = requests.post(url, json={'query': query}, headers=headers, timeout=10)
        if response.status_code != 200: return None, f"HTTP Error {response.status_code}"
        
        data = response.json()
        if "errors" in data: return None, f"GraphQL Error: {data['errors'][0]['message']}"
            
        raw_books = data.get('data', {}).get('me', [])[0].get('user_books', [])
        library = []
        for entry in raw_books:
            try:
                book = entry.get('book', {})
                authors = [c['author']['name'] for c in book.get('contributions', []) 
                          if c.get('author') and c['author'].get('name')]
                author_str = ", ".join(authors) if authors else "Unknown"
                r_date = book.get('release_date', '')
                year = r_date[:4] if r_date else "Unknown"
                
                library.append({
                    "title": book.get('title', 'Unknown'),
                    "author": author_str,
                    "rating": entry.get('rating', 0),
                    "year": year,
                    "full_str": f"{book.get('title')} by {author_str} ({year})"
                })
            except: continue
        return library, None
    except Exception as e: return None, str(e)

# AI recommendation logic
def get_ai_recommendations(api_key, library, filters):
    genai.configure(api_key=api_key)
    model_name = "gemini-3-flash-preview"
    fallback_model = "gemini-1.5-flash"
    
    titles_read = [b['title'] for b in library]
    recent_reads = "\n".join([f"- {b['full_str']} (My Rating: {b['rating']})" for b in library[:60]])
    start_year, end_year = filters['year_range']
    
    prompt = f"""
    Act as an elite literary curator. 
    
    **USER REQUEST:**
    Recommend 5 books matching these strict criteria:
    - **Genre:** {filters['genre']}
    - **Mood:** {filters['mood']}
    - **Length:** ~{filters['pages']} pages
    - **Publication Year:** Must be published between {start_year} and {end_year}
    
    **EXCLUSION LIST:**
    {titles_read}
    
    **USER TASTE PROFILE (Based on recent reads):**
    {recent_reads}
    
    **OUTPUT FORMAT (Markdown Table):**
    | Book Title | Author | Year | Why it fits |
    | :--- | :--- | :--- | :--- |
    | ... | ... | ... | ... |
    """
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text, model_name
    except Exception:
        model = genai.GenerativeModel(fallback_model)
        response = model.generate_content(prompt)
        return response.text, fallback_model

# Initialize credentials
hc_token, gem_key = get_credentials()

with st.sidebar:
    st.header("🧛 Dracula Settings")
    
    st.subheader("Filters")
    f_genre = st.text_input("Genre", "Gothic Horror")
    f_mood = st.text_input("Mood", "Eerie")
    f_pages = st.slider("Max Pages", 200, 1000, 400)
    
    current_year = datetime.now().year
    f_year_range = st.slider(
        "Publication Year", 
        min_value=1800, 
        max_value=current_year, 
        value=(1897, current_year)  # Default to Dracula publication year
    )
    
    st.divider()
    if st.button("Clear Cache"):
        st.cache_data.clear()
        st.rerun()

st.title("📚 Hardcover AI")
st.markdown("Your personal librarian, powered by **Gemini** and your **Hardcover** history.")

if st.button("Analyze & Recommend", type="primary"):
    if not hc_token or not gem_key:
        st.error("⚠️ Missing API Keys. Check sidebar or secrets.toml.")
    else:
        with st.status("Connecting to Neural Network...", expanded=True) as status:
            status.write("📥 Fetching library from Hardcover...")
            library, error = fetch_enhanced_library(hc_token)
            
            if error:
                status.update(label="Connection Failed", state="error")
                st.error(error)
            else:
                status.write(f"🧠 Analyzing {len(library)} books for patterns...")
                filters = {
                    "genre": f_genre, 
                    "mood": f_mood, 
                    "pages": f_pages, 
                    "year_range": f_year_range 
                }
                
                recs, used_model = get_ai_recommendations(gem_key, library, filters)
                
                status.update(label="Complete!", state="complete", expanded=False)
                st.success(f"Generated using **{used_model}** based on {len(library)} read books.")
                st.markdown("### 📖 Top Recommendations")
                st.markdown(recs)