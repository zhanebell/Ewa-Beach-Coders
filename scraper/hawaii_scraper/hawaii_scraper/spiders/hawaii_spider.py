import scrapy
from urllib.parse import urlparse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from ..items import HawaiiScraperItem
from tqdm import tqdm

class HawaiiSpider(CrawlSpider):
    name = "hawaii_spider"

    # Read subdomains from CSV files
    def start_requests(self):
        import csv
        import os
        subdomains = []
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'data')
        csv_files = [
            'hawaii.gov_subdomains.csv',
            'hawaiicounty.gov_subdomains.csv',
            'honolulu.gov_subdomains.csv',
            'ehawaii.gov_subdomains.csv'
        ]
        for file in csv_files:
            file_path = os.path.join(data_dir, file)
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    subdomains.append(f"https://{row['Subdomain']}")

        for url in subdomains:
            yield scrapy.Request(url=url, callback=self.parse_start_url)

    rules = (
        Rule(LinkExtractor(allow=()), callback='parse_item', follow=True),
    )

    def parse_item(self, response):
        item = HawaiiScraperItem()
        item['url'] = response.url
        item['title'] = response.xpath('//title/text()').get()
        paragraphs = response.xpath('//p//text()').getall()
        item['content'] = ' '.join(paragraphs).strip()
        parsed_url = urlparse(response.url)
        item['subdomain'] = parsed_url.netloc
        yield item