import os
import requests
import urllib.parse
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Global storage for user sessions
user_sessions = {}

BASE_URL = "https://www.mp4moviez.now"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Send me a movie name to search.")


# Handle movie name input
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    # If user already selected a movie, treat next input as number
    if user_id in user_sessions and user_sessions[user_id].get("awaiting_choice"):
        try:
            choice = int(text)
            movies = user_sessions[user_id]["movies"]
            if 1 <= choice <= len(movies):
                await send_movie_links(update, movies[choice - 1][1], user_id)
            else:
                await update.message.reply_text("❌ Invalid number.")
        except ValueError:
            await update.message.reply_text("❌ Please send a number.")
        return

    # Otherwise treat as movie search
    search_query = urllib.parse.quote(text)
    search_url = f"{BASE_URL}/search/{search_query}.html"
    response = requests.get(search_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    movie_list = []
    for div in soup.select("div.fl"):
        try:
            a_tag = div.find("a")
            href = a_tag["href"]
            full_link = href if href.startswith("http") else BASE_URL + href
            title = div.find_all("div")[-1].text.strip()
            movie_list.append((title, full_link))
        except Exception:
            continue

    if movie_list:
        msg = "🎬 *Movie Results:*\n\n"
        for i, (title, _) in enumerate(movie_list, start=1):
            msg += f"{i}. {title}\n"
        msg += "\n👉 Send the number of the movie to get download links."

        await update.message.reply_text(msg, parse_mode="Markdown")

        # Save session
        user_sessions[user_id] = {
            "movies": movie_list,
            "awaiting_choice": True
        }
    else:
        await update.message.reply_text("❌ No movies found.")


# Send download links
async def send_movie_links(update: Update, movie_url: str, user_id: int):
    try:
        res = requests.get(movie_url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")

        links_found = False
        for mast_div in soup.select("div.mast"):
            img = mast_div.find("img", alt="Download movie")
            if img:
                a_tag = mast_div.find("a")
                link = a_tag["href"]
                full_link = link if link.startswith("http") else BASE_URL + link
                text = a_tag.text.strip()

                await update.message.reply_text(f"🔗 *{text}*\n{full_link}", parse_mode="Markdown")

                # Try to find direct download link
                src_res = requests.get(full_link, headers=HEADERS)
                src_soup = BeautifulSoup(src_res.text, "html.parser")

                for a in src_soup.find_all("a"):
                    final_href = a.get("href", "")
                    if "download" in final_href or "dl" in final_href:
                        await update.message.reply_text(f"📥 *Final Link:*\n{final_href}", parse_mode="Markdown")
                        links_found = True
                        break

        if not links_found:
            await update.message.reply_text("❌ No final links found.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

    # Clear session
    user_sessions.pop(user_id, None)


# Run the bot
if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot running...")
    app.run_polling()
