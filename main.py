import requests
import parsel
from pprint import pprint
from db import AllFreeNovelsDB
import json
from urls import urls
import argparse


BASE_URL = 'https://www.allfreenovel.com'
DB_NAME = 'allfreenovels.db'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'

def load_urls():
    with open('urls.txt', 'r') as f:
        return f.read().split('\n')

def parse_book(html: str):
    selector = parsel.Selector(text=html)
    book_info = {
        'title': selector.xpath("//h1/a/text()").get('N/A').strip(),
        'author': selector.xpath("//h5[contains(text(), 'Author')]/a/text()").get('N/A'),
        'author_url': selector.xpath("//h5[contains(text(), 'Author')]/a/@href").get('N/A'),
        'categories': selector.xpath("//h5[contains(text(), 'Category')]/a/text()").getall()
    }
    page_count = selector.xpath("//h5[contains(text(), 'Total pages')]/text()").get()
    book_info['page_count'] = int(page_count.split(':')[-1].strip())
    book_info['pages'] = [BASE_URL + i for i in selector.xpath("//div/a[contains(text(), 'Page ')]/@href").getall()]
    return book_info

def parse_page(html: str):
    selector = parsel.Selector(text=html)
    texts = [i.strip() for i in selector.xpath("//p[@class='storyText story-text']/text()").getall() if i != "\r\n                        "]
    return texts

def format_page_texts(texts: list):
    return '\n'.join(texts)
    

def scrape_book_urls():
    with requests.Session() as s:
        s.headers.update({'User-Agent': USER_AGENT})
        for genre in urls.keys():
            print(f"SCRAPING {genre} BOOKS...")
            next_page = urls[genre].strip()
            while next_page:
                print("SCRAPING ", next_page)
                response = s.get(next_page)
                if response.status_code == 200:
                    selector = parsel.Selector(response.text)
                    book_urls = [[BASE_URL + i, genre] for i in set(selector.xpath("//a[contains(@href, '/Book/Details')]/@href").getall())]
                    with AllFreeNovelsDB(DB_NAME) as conn:
                        conn.save_book_urls(book_urls)
                    temp_next_page = selector.xpath("//a[@title='Next Page' and not(contains(@class, 'disabled'))]/@href").get()
                    next_page = None if temp_next_page is None else BASE_URL + temp_next_page
            print(f"FINISHED SCRAPIGN {genre} BOOKS")
def scrape_book_infos():
    books = []
    with AllFreeNovelsDB(DB_NAME) as conn:
        books = conn.get_all_books_with_no_info()
    with requests.Session() as s:
        s.headers.update({'User-Agent': USER_AGENT})
        for book in books:
            print("SEARCHING BOOK INFO ", book['URL'])
            response = s.get(book['URL'])
            if response.status_code == 200:
                book_info = parse_book(response.text)
                with AllFreeNovelsDB(DB_NAME) as conn:
                    conn.save_book_info(book['ID'], json.dumps(book_info))    

def scrape_book_pages():
    books = []
    with AllFreeNovelsDB(DB_NAME) as db:
        books = db.get_all_books_with_info()
    with requests.Session() as s:
        s.headers.update({'User-Agent': USER_AGENT})
        for book in books:
            book_info = json.loads(book['INFO'])
            print(f"GETTING PAGES {book_info['title']}")
            with AllFreeNovelsDB(DB_NAME) as conn:
                page_count_db = conn.count_saved_pages(book['ID'])
                if len(book_info['pages']) == page_count_db:
                    print(f"PAGES ALREADY SCRAPED: {book_info['title']}")
                    continue
                for page_url in book_info['pages']:
                    if not conn.is_page_saved(page_url):
                        print("SCRAPING PAGE: ", page_url)
                        response = s.get(page_url)
                        if response.status_code == 200:
                            page_texts = format_page_texts(parse_page(response.text))
                            conn.save_book_page(book['ID'], page_url, page_texts)
                            print("FINISHED  SCRAPING PAGE ", page_url)
                        else:
                            print(f"ERROR STATUS CODE: {page_url}")
                            
                    else:
                        print("FINISHED SCRAPING PAGE (SKIPPED): ", page_url)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest='command', required=True)
    urlscmd = subparser.add_parser("urls")
    infos = subparser.add_parser("infos")
    pages = subparser.add_parser("pages")
    args = parser.parse_args()
    
    if args.command == 'urls':
        scrape_book_urls()
    elif args.command == 'infos':
        scrape_book_infos()
    elif args.command == 'pages':
        scrape_book_pages()
