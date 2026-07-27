import sqlite3
import datetime
import base64
import requests
from bs4 import BeautifulSoup
import env
import os

DATABASE_NAME = "image.db"


def requests_get(url):
    requests_header={'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}
    req = requests.get(url, headers=requests_header, cookies=env.cookie())    
    return req

class Database():
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_NAME)
        self.cur  = self.conn.cursor()

    def execute(self, sql):
        return self.cur.execute(sql)

    def __del__(self):
        self.conn.commit()
        self.conn.close()

class ImageDB():
    def __init__(self):
        if not os.path.isfile(DATABASE_NAME):
            self.init()
            self.check_and_update()

    def init(self):
        db = Database()
        db.execute(
            "CREATE TABLE images(id INTEGER PRIMARY KEY AUTOINCREMENT, url STRING, base64 STRING, favorite INTEGER, updated DATE)"
        )

    def check_and_update(self, only_newest=False):
        # scraping web page
        page_num = 1
        item_num=1
        created = []
        db = Database()
        while item_num > 0:
            image_urls = []
            url = env.url(page_num)
            req = requests_get(url)
            bsObj = BeautifulSoup(req.text, "html.parser")

            item_num = 0
            fav_main_grid = bsObj.find_all(class_="post-gallery post-gallery-grid post-gallery-150")
            for image_containers in fav_main_grid:
                for link in image_containers.find_all("a"):
                    url = env.base_url() + link.get("href")
                    image_urls.append(url)
                    item_num = item_num + 1
            print(f"get page{page_num} items:{item_num}")
            page_num = page_num+1
            # update db
            created_num=len(created)
            for url in image_urls:
                db.execute("")
                res = db.execute(f'SELECT id FROM images WHERE url="{url}"')
                if res.fetchone() is None:
                    favorite = 0
                    date = datetime.datetime.now()
                    # get image
                    image_base64 = self.get_sankaku_image(url)
                    if image_base64 is None:
                        print(f"  Image:{url} can not get.")
                        continue
                    # insert DB
                    db.execute(f'INSERT INTO images(url, base64, favorite, updated) values("{url}", "{image_base64}", {favorite}, "{date}")')
                    #update_base64(img, db)
                    print(f'CREATE {url}')
                    created.append(url)
                else:
                    print(f"EXIST {url}")
            if only_newest and created_num == len(created):
                break
        print(f"Update Finished. new {len(created)} images.")

    def get_sankaku_image(self, url):
        image_base64 = None
        req = requests_get(url)
        bsObjLink = BeautifulSoup(req.text, "html.parser")
        image_link = bsObjLink.find(id="lowres")
        if image_link is None:
            image_link = bsObjLink.find(id="highres")
        if image_link is None:
            image_link = bsObjLink.find(id="image-link")
        if image_link is not None:
            image_url = image_link.get("href")
            image_url = "https:" + image_url.replace("amp;", "")
            print(f"Image Requests: {image_url}")
            req = requests_get(image_url)
            if 'Content-Type' in req.headers and req.headers['Content-Type'].startswith('image'):
                image_base64 = base64.b64encode(req.content).decode()
            if 'CDN-Status' in req.headers and req.headers['CDN-Status'] == '200':
                image_base64 = base64.b64encode(req.content).decode()

            if image_base64 is None:
                print(req.headers)

        return image_base64

    def get_and_save_image(self, image_url):
        image_base64 = None
        print(f"Image Requests: {image_url}")
        req = requests_get(image_url)
        if 'Content-Type' in req.headers and req.headers['Content-Type'].startswith('image'):
            image_base64 = base64.b64encode(req.content).decode()
        if 'CDN-Status' in req.headers and req.headers['CDN-Status'] == '200':
            image_base64 = base64.b64encode(req.content).decode()
        if image_base64 is None:
            print(req.headers)

        if image_base64 is None:
            print(f"  Image:{image_url} can not get.")
            return None
        # insert DB
        db = Database()
        favorite = 0
        date = datetime.datetime.now()
        res = db.execute(f'SELECT id FROM images WHERE base64="{image_base64}"')
        if res.fetchone() is None:
            print(f"CREATE:{image_url}")
            favorite = 0
            db.execute(f'INSERT INTO images(url, base64, favorite, updated) values("{image_url}", "{image_base64}", {favorite}, "{date}")')
        else:
            print(f"SKIP:Already Saved {image_url}")

        return image_base64


    def get_all(self):
        images = []
        db = Database()
        res = db.execute(f'SELECT id,url,favorite,updated FROM images')
        data = res.fetchall()
        for d in data:
            images.append({'id':d[0], 'url':d[1], 'base64':None, 'favorite':d[2], 'updated':d[3]})
        return images
    

    def get_base64(self, id):
        db = Database()
        res = db.execute(f'SELECT base64 FROM images WHERE id="{id}"')
        data = res.fetchone()
        return data[0]

    def set_favorite(self, url, favorite):
        db = Database()
        db.execute(f'UPDATE images SET favorite="{favorite}" WHERE url="{url}"')

    def get_and_save_local_image(self, path):
        def image_file_to_base64(file_path):
            with open(file_path, "rb") as image_file:
                data = base64.b64encode(image_file.read())

            return data.decode('utf-8')
        date = datetime.datetime.now()
        url = "local://" + str(date)
        image_base64 = image_file_to_base64(path)
        db = Database()

        res = db.execute(f'SELECT id FROM images WHERE base64="{image_base64}"')
        if res.fetchone() is None:
            print(f"CREATE:New local file found {path}")
            favorite = 0
            db.execute(f'INSERT INTO images(url, base64, favorite, updated) values("{url}", "{image_base64}", {favorite}, "{date}")')
        else:
            print(f"SKIP:Already Saved local file {path}")
