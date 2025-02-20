from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time

import urllib.robotparser
from urllib.parse import urlparse

class Worker(Thread):
    def __init__(self, worker_id, config, frontier, crawl_stats=None):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        self.robots_txts = {} # The robots.txt content for each encountered domain/subdomain
        self.crawl_stats = crawl_stats

        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            
            # Download robots.txt if domain/subdomain has not been seen yet
            parsed_url = urlparse(tbd_url)
            domain = parsed_url.netloc.replace("www.", "")
            if domain not in self.robots_txts:
                time.sleep(self.config.time_delay) # Add a delay for politeness
                robots_content = self.get_robots_txt_content(parsed_url)
                self.robots_txts[domain] = robots_content
            
            scraped_urls = scraper.scraper(tbd_url, resp, self.crawl_stats)
            for scraped_url in scraped_urls:
                if self.can_fetch(scraped_url):
                    self.frontier.add_url(scraped_url)

            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay) # Add a delay for politeness

    def get_robots_txt_content(self, parsed_url):
        robots_url = parsed_url.scheme + "://" + parsed_url.netloc + "/robots.txt"
        print(robots_url)
        resp = download(robots_url, self.config, self.logger)

        if resp.status == 200:
            print(resp.raw_response.text)
            return resp.raw_response.text
        return ""
    
    def can_fetch(self, url_to_check):
        parsed_url = urlparse(url_to_check)
        domain = parsed_url.netloc.replace("www.", "")

        if domain in self.robots_txts:
            robots_content = self.robots_txts[domain]
            rp = urllib.robotparser.RobotFileParser()
            rp.parse(robots_content.splitlines())
            return rp.can_fetch(self.config.user_agent, url_to_check)
        return True
