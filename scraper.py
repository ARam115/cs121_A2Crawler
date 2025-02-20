import re
from urllib.parse import urlparse, urldefrag, parse_qs, urljoin
from bs4 import BeautifulSoup

max_size_kb = 2000
max_query_length = 100

valid_domains = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]
paths_to_avoid = ["events", "event/", "tag/", "seminar-series", "explore/department-seminars", "author/"]

def scraper(url, resp, crawl_stats=None):
    links = extract_next_links(url, resp, crawl_stats)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp, crawl_stats=None):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    if resp.status >= 200 and resp.status <= 299:
        # Successful request
        # Check content is not empty
        if resp.raw_response.content is None or len(resp.raw_response.content) == 0:
            return list()
        
        # Avoid crawling very large files
        size_kb = len(resp.raw_response.content) / 1024
        if (size_kb > max_size_kb):
            return list()
        
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        links = []
        # Process page to get page statistics
        # Source: https://realpython.com/python-web-scraping-practical-introduction/
        text_content = soup.get_text()
        # Compute page statistics
        if crawl_stats is not None:
            crawl_stats.compute_page_stats(url, text_content)
        
        # Source: https://medium.com/@spaw.co/extracting-all-links-using-beautifulsoup-in-python-a96786508659
        for a_tag in soup.find_all('a', href=True):
            extracted_url = a_tag.get('href')

            # Defragment the URL
            extracted_url = urldefrag(extracted_url).url

            # Ensure the URL is absolute. Handles cases where URL may be relative by joining it with the base url
            extracted_url = urljoin(url, extracted_url)

            links.append(extracted_url)

        return links
    elif resp.status >= 300 and resp.status <= 399:
        # Requests should redirect automatically
        print(resp.error)
    elif resp.status >= 400 and resp.status <= 599:
        # Failed to get resource
        print(resp.error)
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
        
        domain = parsed.netloc.replace("www.", "")
        # Check appropriate root domain
        valid_subdomain = False
        for d in valid_domains:
            if domain == d or domain.endswith("." + d):
                valid_subdomain = True
        if not valid_subdomain: return False
        
        # Avoid crawler traps
        # 1. Avoid calendars and other pages that lead to events. Examples:
        #   https://ics.uci.edu/events/
        #   https://ics.uci.edu/event/...
        #   https://ics.uci.edu/seminar-series/distinguished-lectures/
        # Avoid low information paths. Tag and author paths may lead to articles that can already be accessed elsewhere
        #   https://ics.uci.edu/tag/...
        #   https://ics.uci.edu/author/... 
        url_path = parsed.path.strip("/")
        for p in paths_to_avoid:
            if url_path.startswith(p):
                return False

        # Avoid links with low information value
        # 1. Certain queries, and long query structures
        query_string = parsed.query
        if query_string:
            # Ignore links with more than two query parameters
            query_params = parse_qs(parsed.query)
            if len(query_params) > 2:
                return False
                    
            # Ignore links with filtering or ordering related queries
            # e.g. See https://ics.uci.edu/people/. This particular path is also filtered out using the robots.txt.
            for param in query_params.keys():
                for ignore_param in ("filter", "limit", "order", "sort"):
                    if param.startswith(ignore_param):
                        return False

        # 2. Avoid instructor/course links (ics domain and path starts with ~) which can have many non-webpage files or many short web pages
        # e.g. http://www.ics.uci.edu/~eppstein/pix leads to crawler trap
        if parsed.path.startswith("/~"):
            return False
        
        # Filter out non-webpage extensions
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4|lif|rle"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|ppsx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|java|php|py|txt|sql|war|apk|rpm"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
