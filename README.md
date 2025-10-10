# iZEV-Eligible-Vehicles-Explorer

Perfect 👍 — here’s a GitHub-ready README.md for your project.
It reads naturally, feels like a developer wrote it by hand, and is formatted with Markdown best practices — including badges, emojis, and example usage.

⸻


# 🇨🇦 iZEV Eligible Vehicles Explorer 🚗⚡  
*A clean, interactive way to explore Transport Canada's Incentives for Zero-Emission Vehicles (iZEV) program data.*

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 🧭 Overview

The **iZEV Explorer** is a small Python + Streamlit web app that lets users **search, filter, and visualize** Canada’s official list of **eligible zero-emission vehicles** under the [Transport Canada iZEV Program](https://tc.canada.ca/en/road-transportation/innovative-technologies/zero-emission-vehicles/incentives-zero-emission-vehicles/eligible-vehicles).

It loads a pre-scraped CSV of all eligible vehicles and provides an intuitive dashboard where you can:

- 🔍 Filter by **Make, Model, Year, Fuel Type**, and more  
- 💰 Compare **incentive amounts** for different lease terms  
- 📅 Browse by **eligibility date range**  
- 📊 View summaries like *Top Makes*, *Fuel Mix*, and *Best Incentives*  
- 💾 Download filtered results as CSV  

---

## 🧱 Project Structure

```bash
izev-explorer/
│
├── scraper.py              # Web scraper (requests + BeautifulSoup)
├── eligible_vehicles_all_pages.csv  # Saved dataset from the Transport Canada site
├── app.py                  # Streamlit web app
├── requirements.txt        # Dependencies
└── README.md               # You're reading this 🙂


⸻

⚙️ Setup Instructions

1️⃣ Clone the repo

git clone https://github.com/yourusername/izev-explorer.git
cd izev-explorer

2️⃣ Install dependencies

pip install -r requirements.txt

Requirements:
	•	Python 3.9+
	•	Streamlit
	•	Pandas
	•	BeautifulSoup4
	•	Requests
	•	Dateutil

3️⃣ Run the app

streamlit run app.py

Then open http://localhost:8501 in your browser.

⸻

🧮 Features

🔹 Smart Filters
	•	Make / Model (linked): Model options change based on the selected Make.
	•	Year range slider: Narrow down by model year.
	•	Fuel type: Filter BEV / PHEV vehicles.
	•	Eligibility date: Choose a date range using a slider.
	•	Incentive amount: Range slider for any-term incentives.
	•	Electric range ≥ 50 km: Toggle to show plug-in hybrids meeting distance criteria.
	•	Free-text search: Search across all columns.

🔹 KPIs

At the top of the app, you’ll see:
	•	Number of Makes
	•	Number of Models
	•	Highest incentive available (any term)

🔹 Data Table
	•	Paginated, sortable, wide-format display
	•	Smart column order (Year → Make → Model → Incentives → Date)
	•	Download filtered data as CSV

🔹 Summary Dashboard

Three tabs with quick insights:
	1.	Top Makes — counts, models, avg/max incentive
	2.	Fuel Mix — BEV vs PHEV distribution + bar chart
	3.	Best Incentives — top 20 vehicles with the highest incentive values

⸻

🧰 Tech Stack

Layer	Technology	Description
Frontend / Backend	Streamlit	Interactive UI + server logic
Data Processing	Pandas	Filtering, aggregations, cleaning
Scraping	Requests, BeautifulSoup	Extracts paginated data from the Transport Canada site
Visualization	Streamlit built-ins	KPIs + charts
Data Format	CSV	Single dataset for fast local use


⸻

🧠 How It Works
	1.	Scraper crawls all pages of Transport Canada’s ZEV eligibility table.
It extracts each table, cleans symbols, converts amounts, and saves everything to eligible_vehicles_all_pages.csv.
	2.	App loads that CSV, detects columns automatically, and builds filters and charts dynamically.
	3.	Users can explore interactively or download filtered results.

⸻

🚀 Deployment

You can easily host this app on:
	•	🟢 Streamlit Community Cloud — free & one-click.
	•	☁️ Google Cloud Run / Heroku / Render — for more control.
	•	🐳 Docker — build once, run anywhere.

Example Dockerfile snippet:

FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]


⸻

💡 Future Improvements
	•	🔁 Auto-refresh scraper weekly to stay current
	•	📈 Trend charts for incentive changes
	•	🧮 Model comparison mode
	•	🌙 Dark theme + branding (Canada/EV style)
	•	📤 Export to Excel with formatting

⸻

🧑‍💻 Author

Your Name
🚗 Electric-mobility enthusiast • 🇨🇦 Canada
💬 Open to ideas, issues, and contributions!

⸻

📜 License

This project is licensed under the MIT License — feel free to use and modify with credit.

⸻

⭐ If you found this helpful…

Give it a star on GitHub! It helps more people discover clean, open-source EV data tools.

---
