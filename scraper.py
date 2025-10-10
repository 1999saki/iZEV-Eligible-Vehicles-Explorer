import time
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import pandas as pd

START_URL = "https://tc.canada.ca/en/road-transportation/innovative-technologies/zero-emission-vehicles/incentives-zero-emission-vehicles/eligible-vehicles"
OUT_CSV   = "eligible_vehicles_all_pages.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; data-extractor/1.0; +https://example.org)"
}

def parse_table(html):
    """
    Return a pandas DataFrame for the first HTML <table> on the page.
    Uses header <th> cells; gracefully handles checkmarks ✓.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return None

    # headers
    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    # Some pages might have multi-row headers; dedupe empties
    headers = [h if h else f"col_{i}" for i, h in enumerate(headers)]

    # rows
    rows = []
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue
        vals = []
        for td in tds:
            # Convert a checkmark to boolean True, blank to False, keep text otherwise
            text = td.get_text(separator=" ", strip=True)
            if text == "✓":
                vals.append(True)
            elif text == "":
                # leave empty as empty string; caller can cast if needed
                vals.append("")
            else:
                vals.append(text)
        # Align lengths if needed
        if len(vals) < len(headers):
            vals += [""] * (len(headers) - len(vals))
        elif len(vals) > len(headers):
            vals = vals[:len(headers)]
        rows.append(vals)

    if not rows:
        return None
    return pd.DataFrame(rows, columns=headers)

def find_next_url(base_url, html):
    """
    Find the absolute URL for the 'Next' pagination link, if present.
    Works with typical 'Next', 'Next ›', '›' labels.
    Returns None if no next link found or it's disabled.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Try common pagination containers
    candidates = []
    candidates += soup.select("nav, div, ul")  # broad but safe

    next_href = None
    for c in candidates:
        # look at anchor tags whose text looks like Next
        for a in c.find_all("a", href=True):
            label = a.get_text(strip=True).lower()
            if label in {"next", "next›", "next »", "›", "next›", "next»"} or "next" in label:
                # If parent LI is disabled, skip
                li = a.find_parent("li")
                if li and ("disabled" in li.get("class", []) or "is-disabled" in li.get("class", [])):
                    continue
                next_href = a["href"]
                break
        if next_href:
            break

    if not next_href:
        # Some sites only expose a numeric pager; pick the current page,
        # then select the following <a> sibling if it exists and is numeric.
        current = soup.select_one("li.active a, li.is-active a, li.active, li.current a")
        if current:
            li = current.find_parent("li") or current
            nxt = li.find_next_sibling("li")
            if nxt:
                a = nxt.find("a", href=True)
                if a:
                    next_href = a["href"]

    if next_href:
        return urljoin(base_url, next_href)
    return None

def scrape_all_pages(start_url, sleep_sec=0.6, max_pages=200):
    url = start_url
    all_frames = []
    seen_urls = set()

    for _ in range(max_pages):
        if url in seen_urls:
            break
        seen_urls.add(url)

        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()

        df = parse_table(r.text)
        if df is not None and not df.empty:
            df["_source_url"] = url
            all_frames.append(df)
            print(f"✓ Parsed {len(df)} rows from {url}")
        else:
            print(f"⚠ No table rows found at {url}")

        nxt = find_next_url(url, r.text)
        if not nxt or nxt == url:
            print("No next page found — finished.")
            break

        url = nxt
        time.sleep(sleep_sec)  # be polite

    if not all_frames:
        return pd.DataFrame()

    # Combine & tidy up
    combined = pd.concat(all_frames, ignore_index=True)

    # Optional: try to coerce money columns to numeric (strip $ and commas)
    money_cols = [c for c in combined.columns if re.search(r"\$|incentive|amount|price", c, re.I)]
    for c in money_cols:
        combined[c] = (
            combined[c]
            .astype(str)
            .str.replace(r"[^\d.\-]", "", regex=True)
            .replace("", pd.NA)
        )
        with pd.option_context("mode.chained_assignment", None):
            combined[c] = pd.to_numeric(combined[c], errors="ignore")

    return combined

if __name__ == "__main__":
    df_all = scrape_all_pages(START_URL)
    print(f"\nTotal rows collected: {len(df_all)}")
    df_all.to_csv(OUT_CSV, index=False)
    print(f"Saved to {OUT_CSV}")
