import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from collections import Counter
import re

# -------------------------
# Scraper
# -------------------------

def scrape_indeed(query, location="London", max_pages=1):
    """
    Scrape Indeed UK for a given query and location.
    max_pages controls how many result pages to scan.
    """
    jobs = []

    for page in range(0, max_pages):
        start = page * 10
        url = f"https://uk.indeed.com/jobs?q={query}&l={location}&start={start}"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        for card in soup.select("div.job_seen_beacon"):
            title_el = card.select_one("h2.jobTitle")
            company_el = card.select_one("span.companyName")
            location_el = card.select_one("div.companyLocation")
            summary_el = card.select_one("div.job-snippet")
            link_el = card.select_one("a")

            title = title_el.get_text(strip=True) if title_el else None
            company = company_el.get_text(strip=True) if company_el else None
            loc = location_el.get_text(strip=True) if location_el else None
            summary = summary_el.get_text(" ", strip=True) if summary_el else None
            link = "https://uk.indeed.com" + link_el["href"] if link_el and link_el.get("href") else None

            if title and company:
                jobs.append({
                    "Title": title,
                    "Company": company,
                    "Location": loc,
                    "Summary": summary,
                    "Link": link
                })

    return pd.DataFrame(jobs)


# -------------------------
# Simple keyword extraction
# -------------------------

def extract_top_keywords(df, column="Summary", top_n=20):
    if column not in df or df.empty:
        return []

    text = " ".join(df[column].dropna().astype(str))
    text = text.lower()
    text = re.sub(r"[^a-z\s+]", " ", text)

    stopwords = set([
        "and", "or", "the", "a", "to", "of", "in", "for", "with", "on", "at",
        "as", "you", "we", "our", "your", "an", "is", "are", "will", "be",
        "team", "role", "experience", "work", "working", "ability", "skills",
        "required", "responsible", "including"
    ])

    words = [w for w in text.split() if w not in stopwords and len(w) > 2]
    counts = Counter(words)
    return counts.most_common(top_n)


# -------------------------
# Streamlit app
# -------------------------

st.set_page_config(
    page_title="London BD/Marketing Job Radar",
    page_icon="📊",
    layout="wide"
)

st.title("📊 London BD/Marketing Job Radar")
st.write("A simple dashboard to see where opportunities are clustering and what skills are in demand.")

# Sidebar controls
st.sidebar.header("Search controls")

role_query = st.sidebar.text_input(
    "Role keywords",
    value="business development director"
)

location_query = st.sidebar.text_input(
    "Location",
    value="London"
)

max_pages = st.sidebar.slider(
    "Pages to scan (Indeed)",
    min_value=1,
    max_value=5,
    value=2,
    help="Each page is ~10 jobs. More pages = slower, but more data."
)

if st.sidebar.button("🔍 Fetch latest jobs"):
    with st.spinner("Scraping Indeed…"):
        query_param = role_query.replace(" ", "+")
        df = scrape_indeed(query_param, location_query, max_pages=max_pages)

        if df.empty:
            st.warning("No jobs found. Try adjusting your search terms or pages.")
        else:
            st.success(f"Fetched {len(df)} roles.")

            st.subheader("📋 Job listings")
            st.dataframe(df, use_container_width=True)

            # Job count by location
            st.subheader("📍 Job count by location")
            loc_counts = df["Location"].value_counts().reset_index()
            loc_counts.columns = ["Location", "Count"]
            st.bar_chart(loc_counts.set_index("Location"))

            # Keyword analysis
            st.subheader("🧠 Top skills/keywords in descriptions")
            top_keywords = extract_top_keywords(df, "Summary", top_n=20)
            if top_keywords:
                kw_df = pd.DataFrame(top_keywords, columns=["Keyword", "Frequency"])
                st.table(kw_df)
            else:
                st.write("No keywords extracted.")

            # Simple filters
            st.subheader("🎯 Filter roles by keyword")
            filter_word = st.text_input("Filter job titles or summaries for a word (e.g. 'AI', 'legal', 'SaaS')")

            if filter_word:
                mask = df["Title"].str.contains(filter_word, case=False, na=False) | \
                       df["Summary"].str.contains(filter_word, case=False, na=False)
                filtered = df[mask]
                st.write(f"Roles matching **{filter_word}**: {len(filtered)}")
                st.dataframe(filtered, use_container_width=True)

else:
    st.info("Set your search terms in the sidebar and click **Fetch latest jobs** to get started.")
