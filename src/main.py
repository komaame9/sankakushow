import flet as ft
import requests
from bs4 import BeautifulSoup
import env
import random

import sqlite3
import datetime
import base64
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
                    image_base64 = self.get_image(url)
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

    def get_image(self, url):
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


    def get_all(self):
        images = []
        db = Database()
        res = db.execute(f'SELECT * FROM images')
        data = res.fetchall()
        for d in data:
            images.append({'id':d[0], 'url':d[1], 'base64':d[2], 'favorite':d[3], 'updated':d[4]})
        return images

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
        

class ImageDic():
    def __init__(self, dic):
        self.dic = dic
    def base64(self):
        return self.dic['base64']
    def url(self):
        return self.dic['url']
    def favorite(self):
        return self.dic['favorite']
    def date(self):
        return self.dic['date']
    def set_favorite(self, favorite=0):
        self.dic['favorite'] = favorite


class ImageList():
    def __init__(self):
        self.reload()
        print(f"Images:{len(self.images)}")

    def next(self) -> ImageDic:
        self.index = self.index + 1
        if self.index >= len(self.images):
            self.index = 0
        return self.now()

    def prev(self) -> ImageDic:
        self.index = self.index - 1
        if self.index < 0:
            self.index = len(self.images)-1
        return self.now()

    def now(self) -> ImageDic :
        return self.images[self.index]
    
    def shuffle(self):
        random.shuffle(self.images)
    
    def update(self, only_newest=False):
        db = ImageDB()
        db.check_and_update(only_newest=only_newest)
        self.images = [ImageDic(i) for i in db.get_all()]

    def reload(self):
        self.index = 0
        db = ImageDB()
        self.images = [ImageDic(i) for i in db.get_all()]

    def length(self) -> int:
        return len(self.images)

    def index(self) -> int:
        return self.index
    
    def all(self):
        return [i.base64() for i in self.images]
    
    def set_index(self, index) -> int:
        self.index = index
        if self.index >= len(self.images):
            self.index = self.images-1
        if self.index < 0:
            self.index = 0
        return self.index
    
    def set_favorite(self, image:ImageDic, favorite=0):
        db = ImageDB()
        db.set_favorite(image.url(), favorite=favorite)
        self.now().set_favorite(favorite)

    def select_list(self, favorite=0):
        self.index = 0
        self.reload()
        self.images = [i for i in self.images if i.favorite()==favorite]
    

class ImageLink():
    def __init__(self, url):
        self.target_url = url
        self.image_url = None

    def url(self):
        if self.image_url != None:
            if not self.isExpired():
                return self.image_url
        return self.get_url()
        
    def get_url(self):
        req = requests_get(self.target_url)
        bsObjLink = BeautifulSoup(req.text, "html.parser")
        image_link = bsObjLink.find(id="lowres")
        if image_link is None:
            image_link = bsObjLink.find(id="highres")
        if image_link is None:
            image_link = bsObjLink.find(id="image-link")
        if image_link is not None:
            image_url = image_link.get("href")
            image_url = image_url.replace("amp;", "")
            self.image_url = "https:" + image_url
        return self.image_url

    def isExpired(self):
        return False

def check_local_images():
    def get_local_files():
        files = ["images/"+file for file in os.listdir("images")]
        files = [file for file in files if os.path.splitext(file)[1] in ('.jpg', '.png', '.gif', '.jpeg')]
        print(f"local file list:{files}")
        return files

    print("check local files")
    db = ImageDB()
    for local_file in get_local_files():
        db.get_and_save_local_image(local_file)


def main(page:ft.Page):
    check_local_images()

    selected_favorite = 0
    images = ImageList()
    if (os.environ.get("SANKAKU_UPDATE")):
        images.update(only_newest=True)
    images.select_list(selected_favorite)
    images.shuffle()
    def set_image():
        image_view.src_base64 = images.now().base64()
        if images.now().favorite() != 0:
            image_view.color = "#808080"
            image_view.color_blend_mode = ft.BlendMode.COLOR
        else:
            image_view.color_blend_mode = ft.BlendMode.DST
        image_view.update()
        nonlocal label
        label.text = images.now().url()
        label.update()

    def on_click_next(e):
        images.next()
        set_image()

    def on_click_prev(e):
        images.prev()
        set_image()

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Arrow Left" :
            on_click_prev(e)
        if e.key == "Arrow Right" :
            on_click_next(e)
        if e.key == "Escape":
            image_view.visible = False
            page.window.visible=False
            page.update()
            page.window.destroy()
        if e.key == "U":
            def on_keyboard_update():
                page.close(dialog)
                modal = ft.AlertDialog(content=ft.Text("Updating..."), modal=True)
                page.open(modal)
                images.update()
                page.close(modal)
            dialog = ft.AlertDialog(title=ft.Text("Update"),
                                    content=ft.Text("Do you want to update Database from Web?"),
                                    actions=[
                                        ft.TextButton("Update", on_click=lambda e: on_keyboard_update()),
                                        ft.TextButton("cancel", on_click=lambda e: page.close(dialog)),
                                    ],
                                    actions_alignment=ft.MainAxisAlignment.END, 
#                                    on_dismiss=lambda e: print("Modal dialog dismissed!"),
                                   )
            page.open(dialog)
        if e.key == "S":
            images.shuffle()
            images.set_index(0)
            set_image()
        if e.key == "D":
            if images.now().favorite() == 0:
                images.set_favorite(images.now(), -1)
            else:
                images.set_favorite(images.now(), 0)
            set_image()
        if e.key == "R":
            images.reload()
            set_image()
        if e.key == "F":
            nonlocal selected_favorite
            if selected_favorite == 0:
                images.select_list(-1)
                selected_favorite = -1
            else:
                images.select_list(0)
                selected_favorite = -0
            set_image()

            

    def on_window_resized(e):
        print("changed", e)
        image_view.width = page.window.width - 50
        image_view.height = page.window.height
        image_view.update()

    def on_click_web(e):
        page.launch_url(label.text)

    page.on_keyboard_event = on_keyboard
    image_view = ft.Image(src_base64=images.now().base64(), fit=ft.ImageFit.CONTAIN, filter_quality=ft.FilterQuality.HIGH)
    if images.now().favorite() != 0:
        image_view.color = "#808080"
        image_view.color_blend_mode = ft.BlendMode.COLOR
    prev_button = ft.IconButton(icon=ft.Icons.SKIP_PREVIOUS, on_click=on_click_prev)
    next_button = ft.IconButton(icon=ft.Icons.SKIP_NEXT, on_click=on_click_next)

    image_container = ft.Row(alignment=ft.MainAxisAlignment.CENTER)
    image_container.controls = [prev_button, image_view, next_button]
    label = ft.TextButton(text=images.now().url(), on_click=on_click_web)

    page.on_resized = on_window_resized

    page.add(
        label,
        image_container,
    )
    page.window.height = 1500
    page.window.width = 1500
    page.window.top =300
    page.window.left = 1000
    page.update()


ft.app(main)
