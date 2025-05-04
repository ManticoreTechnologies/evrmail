import flet as ft

def main(page: ft.Page):
    page.title = "Frameless Test"
    page.window_frameless = True
    page.window_title_bar_hidden = True
    page.window_title_bar_buttons_hidden = True
    page.bgcolor = "#181818"
    page.add(ft.Text("Hello frameless!", color="white"))

ft.app(target=main)
