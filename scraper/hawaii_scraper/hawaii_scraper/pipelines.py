# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class HawaiiScraperPipeline:
    def process_item(self, item, spider):
        return item
import json
import os

class HawaiiScraperPipeline:
    def open_spider(self, spider):
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'data')
        self.file = open(os.path.join(data_dir, 'scraped_data.json'), 'w', encoding='utf-8')
        self.file.write('[')
        self.first_item = True

    def close_spider(self, spider):
        self.file.write(']')
        self.file.close()

    def process_item(self, item, spider):
        import json
        if not self.first_item:
            self.file.write(',\n')
        else:
            self.first_item = False
        line = json.dumps(dict(item), ensure_ascii=False)
        self.file.write(line)
        return item