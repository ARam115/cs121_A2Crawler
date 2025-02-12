import re
from urllib.parse import urlparse, urldefrag, parse_qs, urljoin
import urllib.robotparser
from bs4 import BeautifulSoup
from itertools import islice

max_size_kb = 2000
max_query_length = 100

unique_links = {}
word_frequencies = {}
longest_page = ("", 0)
ics_subdomain_pages = {}

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    if resp.status_code >= 200 and resp.status_code <= 299:
        # Successful request
        # Check content is not empty
        if not resp.content:
            return list()
        
        # Avoid very large files
        size_kb = len(resp.content) / 1024
        if (size_kb > max_size_kb):
            return list()
        
        # TODO: Avoid pages with low information value
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        links = []
        # Process page to get page statistics
        # https://realpython.com/python-web-scraping-practical-introduction/
        text_content = soup.get_text()
        words = text_content.split()

        if len(words) > longest_page[1]:
            longest_page[0] = url

        for w in words:
            word_frequencies[w] += 1

                    
        # TODO: Count subdomains with UNIQUE pages (count these after gathering all)
        parsed = urlparse(url)
        if parsed.netloc.endswith(".ics.uci.edu"):
            ics_subdomain_pages[parsed.netloc] += 1
        
        # TODO: Avoid crawling very large files, especially if they have low information value

        # https://medium.com/@spaw.co/extracting-all-links-using-beautifulsoup-in-python-a96786508659
        for a_tag in soup.find_all('a', href=True):
            extracted_url = a_tag.get('href')

            # Defragment the URL
            extracted_url = urldefrag(extracted_url).url

            # Ensure the URL is absolute. Handles cases where URL may be relative by joining it with the base url
            extracted_url = urljoin(url, extracted_url)

            links.append(extracted_url)

        return links
    elif resp.status_code >= 300 and resp.status_code <= 399:
        # TODO: Detect redirects
        pass
    elif resp.status >= 400 and resp.status <= 599:
        print(resp.raw_response.content)
    elif resp.status >= 600 and resp.status <= 606:
        # Caching specific error. Your crawler is doing something it shouldn't!
        print(resp.error)

    return list()

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        # Check valid scheme
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # Check appropriate root domain
        valid_subdomain = False
        for domain in ("ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"):
            if parsed.netloc.endswith("." + domain):
                valid_subdomain = True
        if not valid_subdomain: return False
        
        
        # Avoid links that could potentially have low information value: Query structure
        query_string = parsed.query
        if query_string:
            # Ignore links with long query strings
            if len(query_string) > max_query_length:
                return False
            
            # Ignore links with filtering or ordering related queries
            # e.g. See https://ics.uci.edu/people/
            query_params = parse_qs(parsed.query)
            for param in query_params.keys():
                for ignore_param in ("filter", "limit", "order", "sort"):
                    if param.startswith(ignore_param):
                        return False
                

        # Filter out non-webpage extensions
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def show_page_statistics():
    # 1. Number of unique pages
    print("Number of unique pages:", len(unique_links))
    print()

    # 2.
    print(f"Longest page is {longest_page[0]} with {longest_page[1]} words")
    print()

    # 3. 50 most common words (ignoring English stop words) ordered with decreasing frequency
    print("50 most common words:")
    ordered_words = dict(sorted(word_frequencies.items(), key=lambda item: item[1]), reverse=True)
    top_50_words = list(islice(ordered_words))
    for word in top_50_words:
        print(word)
    print()

    # 4.
    print("Number of subdomains in ics.uci.edu:", len(ics_subdomain_pages))

    sorted_keys = sorted(ics_subdomain_pages.keys()) # Sort subdomains alphabetically
    ordered_subdomains = {key: ics_subdomain_pages[key] for key in sorted_keys}
    # Show list of subdomains with number of unique pages as URL, number
    for key, value in ordered_subdomains.items():
        print(f"{key}, {value}")

# TODO: Remove
# import requests

# url = 'https://ics.uci.edu/people/'
# reqs = requests.get(url)

# links = extract_next_links(url, reqs)
# print(links)
# print()

# for l in links:
#     if is_valid(l):
#         print(l)

# test_URL = "https://ics.uci.edu/people/?filter%5Bemployee_type%5D%5B0%5D=1096&filter%5Bemployee_type%5D%5B1%5D=1143&filter%5Bemployee_type%5D%5B2%5D=1097"
# print(is_valid(test_URL))

# import time

# import urllib.robotparser

# from utils.download import download
# import requests
# from utils import get_logger, get_urlhash, normalize

# robots_txts = {} # The robots.txt content for each seed URL
# user_agent_to_check = "INF"

# def get_robots_txt_content(url):
#         robots_url = url.rstrip("/") + "/robots.txt"
#         print(robots_url)
#         resp = requests.get(robots_url)

#         if resp.status_code == 200:
#            return resp.text
#         return ""
    
# def can_fetch(url_to_check):
#     parsed_url = urlparse(url_to_check)
#     domain = parsed_url.netloc.replace("www.", "")

#     if domain in robots_txts:
#         robots_content = robots_txts[domain]
#         rp = urllib.robotparser.RobotFileParser()
#         rp.parse(robots_content.splitlines())
#         return rp.can_fetch(user_agent_to_check, url_to_check)
#     return False

# for url in ["https://www.ics.uci.edu","https://www.cs.uci.edu/"]:# ,"https://www.informatics.uci.edu","https://www.stat.uci.edu"
#     robots_content = get_robots_txt_content(url)
#     print(robots_content)
#     if (robots_content):    
#         parsed_url = urlparse(url)
#         domain = parsed_url.netloc.replace("www.", "")

#         print("domain: " + domain)
#         robots_txts[domain] = robots_content
#     time.sleep(0.5)
# print(robots_txts)

# url_to_check = "https://ics.uci.edu/happening"
# allowed = can_fetch(url_to_check)
# print(f"'{user_agent_to_check}' {'is allowed' if allowed else 'is not allowed'} to fetch '{url_to_check}'")
