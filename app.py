import streamlit as st
import requests
import google.generativeai as genai
import json
import re
from datetime import datetime
from openai import OpenAI
from anthropic import Anthropic
import concurrent.futures

# 1. PAGE CONFIG MUST BE FIRST
st.set_page_config(
    page_title="Hardcover AI (Dracula Edition)", 
    page_icon="🧛", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
MAX_WORKERS = 5
RECENT_READS_LIMIT = 60
SEARCH_RESULTS_LIMIT = 5

# --- HELPER: FETCH MODELS ---
@st.cache_data(ttl=3600)
def get_available_gemini_models(api_key):
    """
    Fetches the list of models from the Gemini API that support content generation.
    Filters out 'nano', 'vision', and other non-text-optimized models.
    """
    try:
        genai.configure(api_key=api_key)
        all_models = list(genai.list_models())
        
        # keywords to exclude from the list
        excluded_keywords = ["nano", "vision", "embedding"]
        
        available_models = []
        for m in all_models:
            # 1. Must support content generation
            if 'generateContent' in m.supported_generation_methods:
                name_lower = m.name.lower()
                # 2. Must not contain excluded keywords
                if not any(keyword in name_lower for keyword in excluded_keywords):
                    available_models.append(m.name)

        # Sort to put newer versions (higher numbers) at the top
        available_models.sort(reverse=True)
        return available_models
    except Exception as e:
        return []

# --- AI PROVIDERS ---

class GeminiProvider:
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)
    
    def get_recommendations(self, prompt: str) -> tuple[str, str]:
        try:
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            return response.text, self.model_name
        except Exception as e:
            raise Exception(f"Gemini API error ({self.model_name}): {str(e)}")

class OpenAIProvider:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model_name = "gpt-4o-mini"
    
    def get_recommendations(self, prompt: str) -> tuple[str, str]:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an elite literary curator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content, self.model_name
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

class AnthropicProvider:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model_name = "claude-3-5-sonnet-20241022"
    
    def get_recommendations(self, prompt: str) -> tuple[str, str]:
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text, self.model_name
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

def get_provider(provider_name, api_key, specific_model=None):
    if provider_name == "Gemini":
        # Pass the specific model selected by the user
        return GeminiProvider(api_key, specific_model)
    elif provider_name == "OpenAI":
        return OpenAIProvider(api_key)
    elif provider_name == "Anthropic":
        return AnthropicProvider(api_key)
    
    raise ValueError("Invalid provider selected")

# --- HELPER FUNCTIONS ---

def get_credentials():
    if "hardcover_token" not in st.session_state:
        st.session_state.hardcover_token = ""
    if "gemini_key" not in st.session_state:
        st.session_state.gemini_key = ""
    if "openai_key" not in st.session_state:
        st.session_state.openai_key = ""
    if "anthropic_key" not in st.session_state:
        st.session_state.anthropic_key = ""

    with st.sidebar.expander("🔐 API Credentials", expanded=True):
        st.session_state.hardcover_token = st.text_input(
            "Hardcover Token",
            type="password",
            value=st.session_state.hardcover_token,
        )
        st.session_state.gemini_key = st.text_input(
            "Gemini API Key (optional)",
            type="password",
            value=st.session_state.gemini_key,
        )
        st.session_state.openai_key = st.text_input(
            "OpenAI API Key (optional)",
            type="password",
            value=st.session_state.openai_key,
        )
        st.session_state.anthropic_key = st.text_input(
            "Anthropic API Key (optional)",
            type="password",
            value=st.session_state.anthropic_key,
        )

    return (
        st.session_state.hardcover_token,
        st.session_state.gemini_key,
        st.session_state.openai_key,
        st.session_state.anthropic_key,
    )

@st.cache_data(ttl=1800)
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
            rating
            taggings(limit: 5) { tag { tag } }
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
                community_rating = book.get('rating')
                tags = [t['tag']['tag'] for t in book.get('taggings', []) if t.get('tag')]
                tags_str = ", ".join(tags) if tags else "Untagged"
                
                library.append({
                    "title": book.get('title', 'Unknown'),
                    "author": author_str,
                    "rating": entry.get('rating', 0),
                    "year": year,
                    "community_rating": community_rating,
                    "tags": tags_str,
                    "full_str": f"{book.get('title')} by {author_str} ({year})"
                })
            except: continue
        return library, None
    except Exception as e: return None, str(e)

@st.cache_data(ttl=1800)
def search_hardcover_books(token, title, author=None):
    url = "https://api.hardcover.app/v1/graphql"
    headers = {"authorization": token, "content-type": "application/json"}
    
    title_escaped = title.replace('"', '\\"')
    
    query = f"""
    query SearchBooks {{
      search(
        query: "{title_escaped}"
        query_type: "Book"
        per_page: {SEARCH_RESULTS_LIMIT}
        page: 1
      ) {{
        results
      }}
    }}
    """
    
    try:
        response = requests.post(url, json={'query': query}, headers=headers, timeout=10)
        if response.status_code != 200: 
            return None
        
        data = response.json()
        if "errors" in data:
            return None
        
        search_data = data.get('data', {}).get('search', {})
        results = search_data.get('results', {})
        hits = results.get('hits', [])
        
        if not hits:
            return None
        
        first_hit = hits[0]
        book_data = first_hit.get('document', {})
        return book_data if book_data else None
            
    except Exception as e:
        return None

# NOTE: _provider has an underscore to prevent Streamlit from hashing it
@st.cache_data(ttl=1800)
def get_ai_recommendations(_provider, library, filters):
    titles_read = [b['title'] for b in library]
    recent_reads = "\n".join([f"- {b['full_str']} (My Rating: {b['rating']}/5, Tags: {b['tags']})" for b in library[:RECENT_READS_LIMIT]])
    start_year, end_year = filters['year_range']
    
    prompt = f"""
    Act as an elite literary curator. 
    
    **USER REQUEST:**
    Recommend 10 books matching these strict criteria:
    - **Moods:** {filters['moods']}
    - **Genres:** {filters['genres']}
    - **Length:** ~{filters['pages']} pages
    - **Publication Year:** Must be published between {start_year} and {end_year}
    - **Min Rating:** Must have a rating of {filters['min_rating']} or higher
    
    **EXCLUSION LIST:**
    {titles_read}
    
    **USER TASTE PROFILE (Based on recent reads):**
    {recent_reads}
    
    **OUTPUT FORMAT (JSON Array):**
    Return ONLY a valid JSON array with no markdown, no code blocks. Example:
    [
      {{"title": "Book Title", "author": "Author Name", "reason": "Why it fits"}},
      {{"title": "Another Book", "author": "Another Author", "reason": "Why it fits"}}
    ]
    """
    return _provider.get_recommendations(prompt)

# --- MAIN APP UI ---

# Initialize credentials
hc_token, gemini_key, openai_key, anthropic_key = get_credentials()

with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("🤖 AI Provider")
    available_providers = []
    if gemini_key:
        available_providers.append("Gemini")
    if openai_key:
        available_providers.append("OpenAI")
    if anthropic_key:
        available_providers.append("Anthropic")
    
    if available_providers:
        selected_provider = st.selectbox("Choose AI Provider", available_providers)
        
        # --- NEW: Model Selector for Gemini ---
        selected_gemini_model = None
        if selected_provider == "Gemini":
            with st.spinner("Fetching available Gemini models..."):
                gemini_models = get_available_gemini_models(gemini_key)
                
            if gemini_models:
                # Try to find a good default index
                default_ix = 0
                for i, m in enumerate(gemini_models):
                    if "flash" in m and "1.5" in m: # Prefer 1.5 Flash
                        default_ix = i
                        break
                
                selected_gemini_model = st.selectbox(
                    "Choose Gemini Model", 
                    gemini_models, 
                    index=default_ix
                )
            else:
                st.error("Could not fetch models. Check your API key.")
                selected_gemini_model = "models/gemini-1.5-flash" # Fallback
        # --------------------------------------
        
    else:
        st.error("No API keys configured. Please add at least one API key above.")
        selected_provider = None
    
    st.divider()
    st.subheader("Filters")
    f_moods = st.text_input("Moods (comma-separated)", "Eerie, Dark")
    f_genres = st.text_input("Genres (comma-separated)", "Gothic Horror, Horror")
    f_pages = st.slider("Max Pages", 200, 1000, 400)
    f_min_rating = st.slider("Min Rating", 0.0, 5.0, 3.0, step=0.5)
    
    current_year = datetime.now().year
    f_year_range = st.slider(
        "Publication Year", 
        min_value=1800, 
        max_value=current_year, 
        value=(1897, current_year)
    )
    
    st.divider()
    if st.button("Clear Cache"):
        st.cache_data.clear()
        st.rerun()

st.title("📚 Hardcover AI Librarian")
st.markdown("Your personal librarian, powered by **AI** and your **Hardcover** history.")

if st.button("Analyze & Recommend", type="primary"):
    if not hc_token or not selected_provider:
        st.error("⚠️ Missing API Keys. Please enter your credentials in the sidebar.")
    else:
        with st.status("🪄 Doing my AI Librarian magic...", expanded=True) as status:
            status.write("📥 Fetching your library from Hardcover...")
            library, error = fetch_enhanced_library(hc_token)
            
            if error:
                status.update(label="Connection Failed", state="error")
                st.error(error)
            else:
                status.write(f"🧠 Analyzing {len(library)} books for patterns...")
                filters = {
                    "moods": f_moods,
                    "genres": f_genres, 
                    "pages": f_pages, 
                    "year_range": f_year_range,
                    "min_rating": f_min_rating
                }
                
                # Initialize AI Provider
                try:
                    api_keys_map = {
                        "Gemini": gemini_key,
                        "OpenAI": openai_key,
                        "Anthropic": anthropic_key,
                    }
                    
                    # Pass the specific model if Gemini is selected
                    specific_model = selected_gemini_model if selected_provider == "Gemini" else None
                    
                    provider = get_provider(selected_provider, api_keys_map.get(selected_provider), specific_model)
                    
                    # Call with positional argument (Streamlit maps this to _provider)
                    recs_text, used_model = get_ai_recommendations(provider, library, filters)
                    
                    if not recs_text:
                        raise ValueError("No response from AI provider.")
                        
                except Exception as e:
                    status.update(label="AI Error", state="error")
                    st.error(f"Error calling {selected_provider}: {str(e)}")
                    recs_text = None
                    used_model = "Unknown"

                # Process Recommendations if successful
                if recs_text:
                    status.write("🔍 Verifying books in Hardcover database...")
                    try:
                        # Extract JSON
                        json_match = re.search(r"```json\n(.*)\n```", recs_text, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(1).strip()
                        else:
                            # Try to find array bounds if no markdown tags
                            array_match = re.search(r"\[.*\]", recs_text, re.DOTALL)
                            json_str = array_match.group(0).strip() if array_match else recs_text.strip()
                        
                        recommendations = json.loads(json_str)
                        
                        # Parallel Search
                        results = []
                        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                            future_to_rec = {
                                executor.submit(
                                    search_hardcover_books, 
                                    hc_token, 
                                    rec.get('title', ''), 
                                    rec.get('author', '')
                                ): rec for rec in recommendations
                            }
                            
                            for future in concurrent.futures.as_completed(future_to_rec):
                                rec = future_to_rec[future]
                                try:
                                    book_data = future.result()
                                    if book_data and book_data.get('ratings_count', 0) >= 3:
                                        if len(results) >= 10: break 
                                        
                                        moods_data = book_data.get('moods', [])
                                        moods_str = ", ".join(moods_data[:3]) if moods_data else "—"
                                        genres_data = book_data.get('genres', [])
                                        genres_str = ", ".join(genres_data[:3]) if genres_data else "—"
                                        
                                        rating = book_data.get('rating', 'N/A')
                                        if isinstance(rating, (int, float)):
                                            rating = round(rating, 1)

                                        book_slug = book_data.get('slug', '')
                                        hardcover_link = f"https://hardcover.app/books/{book_slug}" if book_slug else "#"

                                        results.append({
                                            "title": book_data.get('title', rec.get('title')),
                                            "author": rec.get('author', ''),
                                            "rating": rating,
                                            "moods": moods_str,
                                            "genres": genres_str,
                                            "reason": rec.get('reason', ''),
                                            "link": hardcover_link
                                        })
                                except Exception:
                                    continue
                        
                        status.update(label="Complete!", state="complete", expanded=True)
                        st.success(f"Generated using **{used_model}** based on {len(library)} read books.")
                        
                        # Display Results
                        with st.expander("📖 Top Recommendations", expanded=True):
                            if results:
                                table_md = "| Book Title | Author | Rating | Genres | Moods | Why it fits |\n"
                                table_md += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
                                
                                # First 5
                                for r in results[:5]:
                                    title_link = f"[{r['title']}]({r['link']})"
                                    table_md += f"| {title_link} | {r['author']} | {r['rating']} | {r['genres']} | {r['moods']} | {r['reason']} |\n"
                                st.markdown(table_md)
                                
                                # Extra 5
                                if len(results) > 5:
                                    if st.button("✨ Show Extra Recommendations"):
                                        extra_md = "| Book Title | Author | Rating | Genres | Moods | Why it fits |\n"
                                        extra_md += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
                                        for r in results[5:]:
                                            title_link = f"[{r['title']}]({r['link']})"
                                            extra_md += f"| {title_link} | {r['author']} | {r['rating']} | {r['genres']} | {r['moods']} | {r['reason']} |\n"
                                        st.markdown(extra_md)
                            else:
                                st.warning("⚠️ None of the AI recommendations were found in Hardcover's database.")
                        
                    except json.JSONDecodeError as e:
                        status.update(label="Parse Error", state="error")
                        st.error(f"Failed to parse AI response. Raw text below:")
                        st.text_area("Raw Response:", recs_text)