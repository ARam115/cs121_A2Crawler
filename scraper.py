import re
from urllib.parse import urlparse, urldefrag, parse_qs, urljoin
from bs4 import BeautifulSoup
from itertools import islice

max_size_kb = 2000
max_query_length = 100

unique_links = set() # TODO: Add initial links
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

        # TODO: Process page content for 1. statistics 2. avoid crawling very large files, especially if they have low information value
        for link_tag in soup.find_all('a', href=True):
            link = link_tag.get('href')

            # Defragment the URL
            link = urldefrag(link).url
            
            # Ensure the URL path has a trailing '/' for consistency
            parsed = urlparse(link)
            if not parsed.path.endswith('/'):
                link = urljoin(link, '/')

            # Avoid extracting the same link twice. Useful in case the same link appears multiple times in the page and to avoid crawler trap loops
            if link not in unique_links:
                links.append(link)
                unique_links.add(link)
            
            # TODO: robot.txt and sitemaps

            # TODO: Handle relative URLs

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
        
        # Check appropriate domain
        if parsed.netloc not in ("ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"):
            return False
        
        
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
import requests

url = 'https://ics.uci.edu/people/'
reqs = requests.get(url)

links = extract_next_links(url, reqs)
print(links)
print()

for l in links:
    if is_valid(l):
        print(l)

# test_URL = "https://ics.uci.edu/people/?filter%5Bemployee_type%5D%5B0%5D=1096&filter%5Bemployee_type%5D%5B1%5D=1143&filter%5Bemployee_type%5D%5B2%5D=1097"
# print(is_valid(test_URL))
