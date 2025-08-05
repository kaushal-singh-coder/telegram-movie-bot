import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import requests
from bs4 import BeautifulSoup
import urllib.parse

TOKEN = "8249338284:AAHYJTKEm2wjDAdHeM9VeeOW5sdh0gWqpsc"  # Replace with your bot token

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Send me a movie name to search.")

async def handle_movie_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movie_name = update.message.text.strip()
    search_query = urllib.parse.quote(movie_name)
    search_url = f"https://www.mp4moviez.now/search/{search_query}.html"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    movie_list = []
    base_url = "https://www.mp4moviez.now"

    for div in soup.select("div.fl"):
        try:
            a_tag = div.find("a")
            href = a_tag["href"]
            full_link = href if href.startswith("http") else base_url + href

            title_divs = div.find_all("div")
            title = title_divs[-1].text.strip()

            movie_list.append((title, full_link))
        except:
            continue

    if movie_list:
        reply = "🎬 Movie Results:\n\n"
        for i, (title, _) in enumerate(movie_list, start=1):
            reply += f"{i}. {title}\n"
        reply += "\n👉 Send the number of the movie to get download links."
        context.user_data["movie_list"] = movie_list
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text("❌ No movie results found.")

async def handle_movie_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "movie_list" not in context.user_data:
        return

    text = update.message.text.strip()
    if not text.isdigit():
        return

    choice = int(text)
    movie_list = context.user_data["movie_list"]

    if 1 <= choice <= len(movie_list):
        movie_page = movie_list[choice - 1][1]
        headers = {"User-Agent": "Mozilla/5.0"}
        base_url = "https://www.mp4moviez.now"

        response = requests.get(movie_page, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        links_found = False
        for mast_div in soup.select("div.mast"):
            img = mast_div.find("img", alt="Download movie")
            if img:
                a_tag = mast_div.find("a")
                link = a_tag["href"]
                full_link = link if link.startswith("http") else base_url + link
                text = a_tag.text.strip()

                # Visit source link to get final download
                try:
                    src_resp = requests.get(full_link, headers=headers)
                    src_soup = BeautifulSoup(src_resp.text, "html.parser")

                    for a in src_soup.find_all("a"):
                        final_href = a.get("href", "")
                        if final_href and ("download" in final_href or "dl" in final_href):
                            reply = f"🔗 Download
