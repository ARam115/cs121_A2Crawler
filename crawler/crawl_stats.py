from itertools import islice
from urllib.parse import urlparse
import os
import json
import re

class Crawl_Stats():
  def __init__(self, restart):
        self.stats = {
            "total_urls": 0,
            "longest_page": ["", 0],
            "word_frequencies": {},
            "ics_subdomain_pages": {}
        }

        self.stats_save_file = "stats_data.json"
        if restart:
            # Clear the data from the save file
            self._save_data()
        else:
            # Try to load existing data from the save file
            self._load_data()
        
        self.stopwords_file = "english_stopwords.txt"
        self.stopwords = []
        self._retrieve_stop_words()

  def compute_url_stats(self, url):
      # Update total url count
      self.stats["total_urls"] += 1

      # Check whether the url has a subdomain of the ics.uci.edu domain
      parsed = urlparse(url)
      subdomain = parsed.netloc.replace("www.", "")
      if subdomain.endswith("ics.uci.edu"):
          # Update number of pages found for the subdomain
          if subdomain not in self.stats["ics_subdomain_pages"].keys():
              self.stats["ics_subdomain_pages"][subdomain] = 0
          self.stats["ics_subdomain_pages"][subdomain] += 1

      self._save_data()

  def compute_page_stats(self, url, page_content):
      if page_content:
          # Compute page statistics
          words = re.findall(r"[a-zA-Z'-]+", page_content) # We will suppose a word is a sequence of alphabetical chararters, hyphen, or apostrophe
          
          # Number of words
          if len(words) > self.stats["longest_page"][1]:
              self.stats["longest_page"] = [url, len(words)]

          # Frequencies of words
          for w in words:
              if w not in self.stopwords:
                if w not in self.stats["word_frequencies"].keys():
                    self.stats["word_frequencies"][w] = 0
                self.stats["word_frequencies"][w] += 1
          
          self._save_data()
  
  def _save_data(self):
      json_object = json.dumps(self.stats, indent=4)
      with open(self.stats_save_file, "w") as outfile:
          outfile.write(json_object)

  def _load_data(self):
      if os.path.exists(self.stats_save_file):
          with open(self.stats_save_file, 'r') as openFile:
              self.stats = json.load(openFile)
      else:
          self._save_data()
  
  def _retrieve_stop_words(self):
      if os.path.exists(self.stopwords_file):
          with open(self.stopwords_file, 'r') as openFile:
              for line in openFile:
                  word = line.strip()
                  self.stopwords.append(word)
      
  def print_total_urls(self):
      total_urls = self.stats["total_urls"]
      print(f"{total_urls} total urls discovered")

  def print_longest_page(self):
      url = self.stats["longest_page"][0]
      word_count = self.stats["longest_page"][1]
      print(f"Longest page is {url} with {word_count} words")

  def print_most_common_words(self):
      # 50 most common words (ignoring English stop words) ordered with decreasing frequency
      print("50 most common words:")
      ordered_words = dict(sorted(self.stats["word_frequencies"].items(), key=lambda item: item[1], reverse=True))
      top_50_words = list(islice(ordered_words, 50))
      for word in top_50_words:
          print(word)

  def print_ics_subdomains(self):
      print("Number of subdomains in ics.uci.edu discovered:", len(self.stats["ics_subdomain_pages"]))

      sorted_keys = sorted(self.stats["ics_subdomain_pages"].keys()) # Sort subdomains alphabetically
      ordered_subdomains = {key: self.stats["ics_subdomain_pages"][key] for key in sorted_keys}
      # Show list of subdomains with number of unique pages as URL, number
      for key, value in ordered_subdomains.items():
          print(f"{key}, {value}")

  def print_all_stats(self):
      self.print_total_urls()
      self.print_longest_page()
      self.print_most_common_words()
      self.print_ics_subdomains()

def main():
    crawl_stats = Crawl_Stats(True)
    # crawl_stats.compute_page_stats("url", "can't How many unique pages did you find? Uniqueness for the purposes of this assignment is ONLY established by the URL, but discarding the fragment part. So, for example, http://www.ics.uci.edu#aaa and http://www.ics.uci.edu#bbb are the same URL. Even if you implement additional methods for textual similarity detection, please keep considering the above definition of unique pages for the purposes of counting the unique pages in this assignment.")
    crawl_stats.compute_url_stats("https://ics.uci.edu/people/")
    crawl_stats.compute_url_stats("https://www.ics.uci.edu")
    crawl_stats.compute_url_stats("https://ics.uci.edu/")
    crawl_stats.compute_url_stats("http://vision.ics.uci.edu")
    crawl_stats.print_all_stats()

if __name__ == "__main__":
    main()
