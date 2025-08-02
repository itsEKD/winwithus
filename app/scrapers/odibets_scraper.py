from flask import Flask
from flask_pymongo import PyMongo
from playwright.sync_api import sync_playwright
from datetime import datetime
from dotenv import load_dotenv
import os, time

# Load env variables
load_dotenv()

# Set up Flask app and Mongo
app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

def scrape_odibets_odds():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://odibets.com/")

        time.sleep(5)  # Let the odds load

        games = page.query_selector_all("div.game.e")
        scraped = []

        for game in games:
            try:
                match = game.query_selector("div.t-l").inner_text()
                league = game.query_selector("div.l").inner_text()
                markets = []

                # Odds (1X2 market)
                odds_block = game.query_selector("div.b-m.m2")
                if odds_block:
                    options = odds_block.query_selector_all("small.t")
                    odds = odds_block.query_selector_all("span.b")

                    for i in range(len(options)):
                        label = options[i].inner_text().strip()
                        value = odds[i].inner_text().strip()
                        markets.append({"option": label, "odd": float(value)})

                scraped.append({
                    "match": match,
                    "league": league,
                    "markets": markets,
                    "scraped_at": datetime.utcnow()
                })

            except Exception as e:
                print("❌ Error on game:", e)
                continue

        with app.app_context():
            db_name = os.getenv("DB_NAME")
            collection = mongo.cx[db_name].odibets_odds
            collection.delete_many({})
            if scraped:
                collection.insert_many(scraped)
                print(f"✅ Inserted {len(scraped)} games into '{db_name}.odibets_odds'")
            else:
                print("⚠️ No odds scraped.")

        browser.close()

if __name__ == "__main__":
    scrape_odibets_odds()
