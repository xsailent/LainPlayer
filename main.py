import httpx
from bs4 import BeautifulSoup
import time
import os
import mpv
import subprocess
import yt_dlp
import ui
from ui import LainPlayerUI
import threading
import asyncio
from textual import work
from textual.widgets import Label, ListItem, ListView

# адрес который будет задействован
address = 'https://lainlife.org'
LOGIN_PAGE_URL = f'{address}/'
LOGIN_ACTION_URL = f'{address}/login'
music_adr = "https://lainlife.org/search"

filename = "lainplayer.mp3"
save_path = os.path.join("/tmp", filename)

def label_list_box(item, app):
    url = item.track_url

    music_thread = threading.Thread(
        target=download_and_play,
        args=(url, item.app), 
        daemon=True
    )
    music_thread.start()

def download_and_play(mpd_url, app):
    output_path = '/tmp/lainplayer.mp3'

    app.call_from_thread(
        app.notify, 
        "Запрос отправлен в yt-dlp. Начинаю скачивание аудио...",
        title="Загрузка"
    )

    # 1. Скачивание и конвертация в MP3
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '/tmp/lainplayer.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'overwrites': True,
        'quiet': True,
    }

    #print("Скачивание аудио...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([mpd_url])

    if not os.path.exists(output_path):
        print(f"Ошибка: файл {output_path} не найден.")
        return

    # 2. Воспроизведение через mpv
    app.call_from_thread(
        app.notify,
        "Файл успешно сконвертирован. Передаю поток в mpv.",
        title="Воспроизведение",
        severity="info"
    )
    player = mpv.MPV(video=False, ytdl=False)  # Отключаем видео и встроенный ytdl
    player.play(output_path)

    # Ожидаем окончания воспроизведения
    player.wait_for_playback()

# Декоратор @work превращает функцию в фоновый процесс Textual
async def load_music(app):
    login_email = ui.login_email
    login_password = ui.login_password

    # запуск клиента httpx
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # делаем зпапрос на страницу авторизации
        response = await client.get(LOGIN_PAGE_URL)
        soup = BeautifulSoup(response.text, "html.parser")
    
        # ищем скрытое поле hash
        hash_element = soup.find("input", {"name": "hash"})
        if not hash_element:
            print("Не удалось найти скрытое поле 'hash' на странице!")
            exit()

        hash_value = hash_element.get("value")
    
        # информация для входа
        form_fields = {
            "login": (None, login_email),
            "password": (None, login_password),
            "jReturnTo": (None, "/"),
            "hash": (None, hash_value)
        }

        # юзер агент(хз зачем, мб потом уберу)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
        # пост запрос на вход в акк
        login_response = await client.post(LOGIN_ACTION_URL, files=form_fields, headers=headers)

        params = {
            "section": "audios",
            "q": "",
            "p": 1, 
        }
    
        # добавляем словарь чтобы удобно обращаться к адресу для скачивания файла по названию 
        tracks_urls = {}

        while True:
            # запрос на страницу с музыкой и вывод статуса
            music_response = await client.get(music_adr, params=params)
            music_soup = BeautifulSoup(music_response.text, "html.parser")

            # создаем проверку есть ли div поиска на сайте
            target_div = None
            parent = music_soup.find('div', id='search_page')
        
            if parent:
                # ищем div с треками
                target_div = parent.find('div', class_='page_wrap_content_main')
        
                if target_div:
                    audio_tracks = target_div.find_all('div', class_='scroll_node')
                
                    # создаем список треков и выводим
                    for track in audio_tracks:
                        # находим div с классом audioEmbed и выводим data-name(название трека с исполнителем) в консоль
                        audio_embed = track.find('div', class_="audioEmbed")
                    
                        if audio_embed:
                            name = audio_embed.get('data-name')
                            url = audio_embed.get('data-url')

                            track_url = url
                                
                            list_view = app.query_one("#my_list", ListView)

                            item = ListItem(Label(name))

                            # Сохраняем имя и ссылку на аудио прямо внутри объекта!
                            item.track_name = name      
                            item.track_url = track_url  

                            # Добавляем в список
                            list_view.append(item)

            # увелечиваем значение p чтобы загрузить новые треки и делаем паузу чтобы сервер не перетруждался
            params["p"] += 1
            await asyncio.sleep(1)

app = LainPlayerUI(
    action_function=label_list_box,
    setup_worker=load_music
)

if __name__ == "__main__":
    #ui.start_player()
    app.run()
