import flet as ft
import random

import os
import database

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
        db = database.ImageDB()
        db.check_and_update(only_newest=only_newest)
        self.images = [ImageDic(i) for i in db.get_all()]

    def reload(self):
        self.index = 0
        db = database.ImageDB()
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
        db = database.ImageDB()
        db.set_favorite(image.url(), favorite=favorite)
        self.now().set_favorite(favorite)

    def select_list(self, favorite=0):
        self.index = 0
        self.reload()
        self.images = [i for i in self.images if i.favorite()==favorite]
    

def check_local_images():
    def get_local_files():
        files = ["images/"+file for file in os.listdir("images")]
        files = [file for file in files if os.path.splitext(file)[1] in ('.jpg', '.png', '.gif', '.jpeg')]
        print(f"local file list:{files}")
        return files

    print("check local files")
    db = database.ImageDB()
    for local_file in get_local_files():
        db.get_and_save_local_image(local_file)


def app_main(page:ft.Page):
    check_local_images()

    selected_favorite = 0
    images = ImageList()
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


def main(page:ft.Page):
    if (os.environ.get("IMAGE_SAVE_MODE")):
        blank_image="R0lGODlhAQABAGAAACH5BAEKAP8ALAAAAAABAAEAAAgEAP8FBAA7"
        def on_keyboard(e: ft.KeyboardEvent):
            if e.key == "Escape":
                image.visible = False
                page.window.visible=False
                page.update()
                page.window.destroy()
            if e.key == "C":
                image.src_base64=blank_image
                image.update()

        page.on_keyboard_event = on_keyboard
        def on_submit(e):
            url_field.read_only=True
            url_field.update()
            message.visible=True
            message.update()
            db = database.ImageDB()
            ret = db.get_and_save_image(url_field.value)
            if ret:
                image.src_base64 = ret
                image.update()
            url_field.read_only=False
            url_field.value=""
            url_field.update()
            message.visible=False
            message.update()
        def on_focus(e:ft.WindowEvent):
            if e.type is ft.WindowEventType.FOCUS:
                url_field.focus()
                url_field.update()

        url_field = ft.TextField(label="image url", on_submit=on_submit)
        image = ft.Image(src_base64=blank_image, fit=ft.ImageFit.CONTAIN, filter_quality=ft.FilterQuality.HIGH, width=640, height=640)
        message = ft.Text(value="Loading", visible=False)
        row = ft.Row(controls=[image])
        page.add(url_field, message, row)
        page.window.width = 640
        page.window.height = 700
        page.window.on_event = on_focus
        page.update()
    else:
        app_main(page)

ft.app(main)
