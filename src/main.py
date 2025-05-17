import flet as ft
import requests
from bs4 import BeautifulSoup
import env
import random

class ImageList():
    def __init__(self):
        self.srcs=[]
        self.index = -1

        page_num = 1
        item_num = 1

        while item_num > 0:
            url = env.url(page_num)
            req = requests.get(url, cookies=env.cookie())
            bsObj = BeautifulSoup(req.text, "html.parser")

            item_num = 0
            for image_containers in bsObj.find_all(class_="post-preview-container"):
                for link in image_containers.find_all("a"):
                    url = env.base_url() + link.get("href")
                    self.srcs.append(ImageLink(url))
                    item_num = item_num + 1
            print(f"get page{page_num} items:{item_num}")
            page_num = page_num+1

        random.shuffle(self.srcs)

    async def next(self):
        self.index = self.index + 1
        if self.index >= len(self.srcs):
            self.index = 0
        link = self.srcs[self.index]
        while link.url() is None:
            print(f"removed {link.target_url}, items:{len(self.srcs)}")
            self.srcs.remove(link)
            if self.index >= len(self.srcs):
                return None
            link =self.srcs[self.index]
        return link.url()

    def prev(self):
        self.index = self.index - 1
        if self.index < 0:
            self.index = len(self.srcs)-1
        link = self.srcs[self.index]
        while link.url() is None:
            print(f"removed {link.target_url}, items:{len(self.srcs)}")
            self.srcs.remove(link)
            if self.index >= len(self.srcs):
                return None
            link =self.srcs[self.index]
        return link.url()


    

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
        req = requests.get(self.target_url, cookies=env.cookie())
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


def main(page: ft.Page):
    images = ImageList()
    def on_click_next(e):
        image_view.src = images.next()
        image_view.update()
        nonlocal label
        label.value = image_view.src
        label.update()

    def on_click_prev(e):
        image_view.src = images.prev()
        image_view.update()
        nonlocal label
        label.value = image_view.src
        label.update()

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Arrow Left" :
            on_click_prev(e)
        if e.key == "Arrow Right" :
            on_click_next(e)
        if e.key == "Escape":
            page.window.visible=False
            page.update()
            page.window.destroy()
        #print(e.key)

    def on_window_resized(e):
        print("changed", e)
        image_view.width = page.window.width - 50
        image_view.height = page.window.height
        image_view.update()

    page.on_keyboard_event = on_keyboard
    image_view = ft.Image(src=images.next(), fit=ft.ImageFit.CONTAIN)
    prev_button = ft.IconButton(icon=ft.Icons.SKIP_PREVIOUS, on_click=on_click_prev)
    next_button = ft.IconButton(icon=ft.Icons.SKIP_NEXT, on_click=on_click_next)

    image_container = ft.Row(alignment=ft.MainAxisAlignment.CENTER)
    image_container.controls = [prev_button, image_view, next_button]
    label = ft.Text(value=image_view.src)

    page.on_resized = on_window_resized


    page.add(
        label,
        image_container
    )
    page.window.height = 1500
    page.window.width = 1500
    page.update()


ft.app(main)
