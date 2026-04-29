import requests
from bs4 import BeautifulSoup

def crawl(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text()
    links = [a.get("href") for a in soup.find_all("a")]

    return text, links