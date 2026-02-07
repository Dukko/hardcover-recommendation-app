import streamlit as st
import requests
import google.generativeai as genai
import json
from datetime import datetime
from abc import ABC, abstractmethod
from openai import OpenAI
from anthropic import Anthropic

import streamlit as st
import requests
import google.generativeai as genai
import json
from datetime import datetime
from abc import ABC, abstractmethod
from openai import OpenAI
from anthropic import Anthropic

# AI Provider Abstract Base Class
class AIProvider(ABC):
    @abstractmethod
    def get_recommendations(self, prompt: str) -> tuple[str, str]:
        """Returns (response_text, model_name)"""
        pass

# Gemini Provider
class GeminiProvider(AIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
    
    def get_recommendations(self, prompt: str) -> tuple[str, str]:
        model_name = "gemini-3-flash-preview"
        fallback_model = "gemini-2.0-flash"
        
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text, model_name
        except Exception:
            model = genai.GenerativeModel(fallback_model)
            response = model.generate_content(prompt)
            return response.text, fallback_model

# OpenAI Provider
class OpenAIProvider(AIProvider):
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

# Anthropic Provider
class AnthropicProvider(AIProvider):
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
    
    # Get API keys for all providers
    gemini_key = st.secrets.get("connections", {}).get("gemini_key", "")
    openai_key = st.secrets.get("connections", {}).get("openai_key", "")
    anthropic_key = st.secrets.get("connections", {}).get("anthropic_key", "")
    
    if not hc_token or not (gemini_key or openai_key or anthropic_key):
        with st.sidebar.expander("🔐 API Credentials", expanded=True):
            st.caption("Secrets not found. Enter manually.")
            if not hc_token: 
                hc_token = st.text_input("Hardcover Token", type="password")
            if not gemini_key: 
                gemini_key = st.text_input("Gemini API Key (optional)", type="password")
            if not openai_key: 
                openai_key = st.text_input("OpenAI API Key (optional)", type="password")
            if not anthropic_key: 
                anthropic_key = st.text_input("Anthropic API Key (optional)", type="password")
    
    return hc_token, gemini_key, openai_key, anthropic_key

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

# Search for books in Hardcover database
def search_hardcover_books(token, title, author=None):
    url = "https://api.hardcover.app/v1/graphql"
    headers = {"authorization": token, "content-type": "application/json"}
    
    # Escape special characters in title for GraphQL
    title_escaped = title.replace('"', '\\"')
    
    # Use the search endpoint - request basic fields
    query = f"""
    query SearchBooks {{
      search(
        query: "{title_escaped}"
        query_type: "Book"
        per_page: 5
        page: 1
      ) {{
        ids
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
        
        # Extract the document from the first hit
        first_hit = hits[0]
        book_data = first_hit.get('document', {})
        
        return book_data if book_data else None
            
    except Exception as e:
        return None

# AI recommendation logic
def get_ai_recommendations(provider: AIProvider, library, filters):
    titles_read = [b['title'] for b in library]
    recent_reads = "\n".join([f"- {b['full_str']} (My Rating: {b['rating']}/5, Tags: {b['tags']})" for b in library[:60]])
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
    
    return provider.get_recommendations(prompt)

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
        value=(1897, current_year)  # Default to Dracula publication year
    )
    
    st.divider()
    if st.button("Clear Cache"):
        st.cache_data.clear()
        st.rerun()

st.title("📚 Hardcover AI Librarian")
st.markdown("Your personal librarian, powered by **AI** and your **Hardcover** history.")

if st.button("Analyze & Recommend", type="primary"):
    if not hc_token or not selected_provider:
        st.error("⚠️ Missing API Keys. Check sidebar or secrets.toml.")
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
                
                # Initialize the selected AI provider
                try:
                    if selected_provider == "Gemini":
                        provider = GeminiProvider(gemini_key)
                    elif selected_provider == "OpenAI":
                        provider = OpenAIProvider(openai_key)
                    elif selected_provider == "Anthropic":
                        provider = AnthropicProvider(anthropic_key)
                    else:
                        raise ValueError("No provider selected")
                    
                    recs_text, used_model = get_ai_recommendations(provider, library, filters)
                except Exception as e:
                    status.update(label="AI Error", state="error")
                    st.error(f"Error calling {selected_provider}: {str(e)}")
                    recs_text = None
                
                if recs_text:
                    # Parse AI recommendations and lookup in Hardcover
                    status.write("🔍 Verifying books in Hardcover database...")
                    
                    try:
                        # Extract JSON from response
                        json_str = recs_text.strip()
                        if json_str.startswith('```'):
                            json_str = json_str.split('```')[1]
                            if json_str.startswith('json'):
                                json_str = json_str[4:]
                        
                        recommendations = json.loads(json_str)
                        
                        # Lookup each book in Hardcover and build results table
                        # Filter to recommendations with 3+ ratings and take up to 10
                        results = []
                        for rec in recommendations:
                            if len(results) >= 10:
                                break
                            book_data = search_hardcover_books(hc_token, rec.get('title', ''), rec.get('author', ''))
                            if book_data and book_data.get('ratings_count', 0) >= 3:
                                # Extract moods from search API (limit to top 3)
                                moods_data = book_data.get('moods', [])
                                moods_str = ", ".join(moods_data[:3]) if moods_data else "—"
                                
                                # Extract genres from search API (limit to top 3)
                                genres_data = book_data.get('genres', [])
                                genres_str = ", ".join(genres_data[:3]) if genres_data else "—"
                                
                                # Round rating to 1 decimal place
                                rating = book_data.get('rating', 'N/A')
                                if isinstance(rating, (int, float)):
                                    rating = round(rating, 1)
                                
                                # Get hardcover link from slug
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
                        
                        status.update(label="Complete!", state="complete", expanded=True)
                        st.success(f"Generated using **{used_model}** based on {len(library)} read books.")
                        
                        # Display results in expanded container
                        with st.expander("📖 Top Recommendations", expanded=True):
                            # Display as markdown table
                            if results:
                                # Always show first 5
                                table_md = "| Book Title | Author | Rating | Genres | Moods | Why it fits |\n"
                                table_md += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
                                for r in results[:5]:
                                    title_link = f"[{r['title']}]({r['link']})"
                                    table_md += f"| {title_link} | {r['author']} | {r['rating']} | {r['genres']} | {r['moods']} | {r['reason']} |\n"
                                st.markdown(table_md)
                                
                                # Show button for extra recommendations if available
                                if len(results) > 5:
                                    if st.button("✨ Show Extra Recommendations"):
                                        extra_md = "| Book Title | Author | Rating | Genres | Moods | Why it fits |\n"
                                        extra_md += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
                                        for r in results[5:]:
                                            title_link = f"[{r['title']}]({r['link']})"
                                            extra_md += f"| {title_link} | {r['author']} | {r['rating']} | {r['genres']} | {r['moods']} | {r['reason']} |\n"
                                        st.markdown(extra_md)
                            else:
                                st.warning("⚠️ None of the AI recommendations were found in Hardcover's database. Try different filters or moods.")
                        
                    except json.JSONDecodeError as e:
                        status.update(label="Parse Error", state="error")
                        st.error(f"Failed to parse AI response as JSON: {str(e)}")
                        st.text_area("Raw Response:", recs_text)