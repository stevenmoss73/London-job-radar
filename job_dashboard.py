import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# -----------------------------
# Reed.co.uk Scraper (Reliable)
# -----------------------------
def scrape_reed(query, location="London", max_pages=1):
    jobs = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    for page in range(1, max_pages + 1):
        url = (
            f"https://www.reed.co.uk/jobs/{query}-jobs-in-{location}?pageno={page}"
        )

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        cards = soup.select("article.job-result")

        for card in cards:
            title = card.select_one("h3.title a")
            company = card.select_one("a.gtmu-js-job-result-company")
            loc = card.select_one("li.location")
            snippet = card.select_one("div.description")
            link = title["href"] if title else None

            jobs.append({
                "Title": title.get_text(strip=True) if title else None,
                "Company": company.get_text(strip=True) if company else None,
                "Location": loc.get_text(strip=True) if loc else None,
                "Summary": snippet.get_text(" ", strip=True) if snippet else None,
                "Link": "https://www.reed.co.uk" + link if link else None
            })

    return pd.DataFrame([j for j in jobs if j["Title"]])


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="London BD/Marketing Job Radar", layout="wide")

st.title("📊 London BD/Marketing Job Radar")
st.write("Live job scraping dashboard for BD, Marketing, and Client Development roles in London.")

# Sidebar inputs
st.sidebar.header("Search Settings")
query_param = st.sidebar.text_input("Job Title / Keywords", "business development")
location_query = st.sidebar.text_input("Location", "London")
max_pages = st.sidebar.slider("Pages to scrape", 1, 5, 1)

run_search = st.sidebar.button("Fetch Latest Jobs")

# -----------------------------
# Run scraper
# -----------------------------
if run_search:
    st.write("🔍 Fetching jobs… please wait.")

    df = scrape_reed(query_param.replace(" ", "-"), location_query.replace(" ", "-"), max_pages=max_pages)

    if df.empty:
        st.warning("No jobs found. Try broader keywords.")
    else:
        st.success(f"Found {len(df)} jobs.")
        st.dataframe(df)

        # Download button
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download results as CSV", csv, "jobs.csv", "text/csv")

else:
    st.info("Enter your search terms and click 'Fetch Latest Jobs' to begin.")
