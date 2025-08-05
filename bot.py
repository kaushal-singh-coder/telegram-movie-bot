import requests
from bs4 import BeautifulSoup
import urllib.parse

# Input movie name
movie_name = input("Enter movie name to search: ")
search_query = urllib.parse.quote(movie_name)
search_url = f"https://www.mp4moviez.now/search/{search_query}.html"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

print(f"\n🔍 Searching: {search_url}")

# Fetch search page
response = requests.get(search_url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

movie_list = []
base_url = "https://www.mp4moviez.now"

print("\n🎬 Movie Results:\n")
for i, div in enumerate(soup.select("div.fl"), start=1):
    try:
        a_tag = div.find("a")
        href = a_tag["href"]
        full_link = href if href.startswith("http") else base_url + href

        title_divs = div.find_all("div")
        title = title_divs[-1].text.strip()

        img = div.find("img")
        img_src = img["src"]
        img_full = base_url + img_src if img_src.startswith("/") else img_src

        movie_list.append((title, full_link, img_full))

        print(f"{i}. 🎬 {title}")
        print(f"   🔗 Link: {full_link}")
        print(f"   🖼️ Poster: {img_full}\n")
    except Exception as e:
        print(f"❌ Skipped due to error: {e}")

# Ask user which movie to open
if movie_list:
    try:
        choice = int(input("👉 Enter the number of the movie you want to open: "))
        if 1 <= choice <= len(movie_list):
            movie_page = movie_list[choice - 1][1]
            print(f"\n✅ Opening: {movie_page}")
            response = requests.get(movie_page, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")

            download_links = []

            for mast_div in soup.select("div.mast"):
                img = mast_div.find("img", alt="Download movie")
                if img:
                    a_tag = mast_div.find("a")
                    link = a_tag["href"]
                    full_link = link if link.startswith("http") else base_url + link
                    text = a_tag.text.strip()
                    download_links.append((text, full_link))

            if download_links:
                print("\n⬇️ Download Source Pages:\n")
                for i, (text, link) in enumerate(download_links, start=1):
                    print(f"{i}. {text}")
                    print(f"   🔗 Source Link: {link}")

                    try:
                        src_resp = requests.get(link, headers=headers)
                        src_soup = BeautifulSoup(src_resp.text, "html.parser")

                        found = False
                        for a in src_soup.find_all("a"):
                            final_href = a.get("href", "")
                            if final_href and ("download" in final_href or "dl" in final_href or "files" in final_href):
                                final_headers = {
                                    "User-Agent": headers["User-Agent"],
                                    "Referer": link
                                }
                                test = requests.head(final_href, headers=final_headers)
                                if test.status_code == 200:
                                    print(f"   ✅ Final Download Link (Works in browser): {final_href}")
                                    print(f"   📥 Use this in Termux:\nwget --header=\"Referer: {link}\" --user-agent=\"{headers['User-Agent']}\" \"{final_href}\"\n")
                                    found = True
                        if not found:
                            print("   ❌ No final link found.\n")

                    except Exception as e:
                        print(f"   ❌ Error visiting source: {e}\n")
            else:
                print("❌ No download links found on movie page.")
        else:
            print("❌ Invalid choice.")
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
else:
    print("❌ No movie results found.")
