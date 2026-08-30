import httpx
from bs4 import BeautifulSoup
import time
import os
import mpv
import subprocess
import yt_dlp
import ui
import pytermgui as ptg
import threading

# адрес который будет задействован
address = 'https://lainlife.org'
LOGIN_PAGE_URL = f'{address}/'
LOGIN_ACTION_URL = f'{address}/login'
music_adr = "https://lainlife.org/search"

filename = "lainplayer.mp3"
save_path = os.path.join("/tmp", filename)

#login = ui.start_player().email_field.value
#password = ui.start_player().password_field.value

def login(email, password):
    global login_email, login_password
    login_email = email
    login_password = password
    main()  # Запускаем основную функцию

def download_and_play(mpd_url):
    output_path = '/tmp/lainplayer.mp3'

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
        'quiet': True,  # Скрыть лишний вывод yt-dlp в консоли
    }

    print("Скачивание аудио...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([mpd_url])

    if not os.path.exists(output_path):
        print(f"Ошибка: файл {output_path} не найден.")
        return

    # 2. Воспроизведение через mpv
    print(f"Воспроизведение: {output_path}")
    player = mpv.MPV(video=False, ytdl=False)  # Отключаем видео и встроенный ytdl
    player.play(output_path)

    # Ожидаем окончания воспроизведения
    player.wait_for_playback()

def add_track_to_list(name, track_url):
    """Добавляет трек в список"""
    global track_container
    
    if track_container is None:
        return
    
    button = ptg.Button(
        f"🎵 {name}", 
        lambda _: threading.Thread(target=download_and_play, args=(track_url,), daemon=True).start()
    )
    
    # Добавляем в контейнер
    track_container._widgets.append(button)
    
    # Обновляем максимальную прокрутку
    track_container._max_scroll = max(0, len(track_container._widgets) - track_container.height + 1)

def load_music():
    global login_email, login_password

    # запуск клиента httpx
    with httpx.Client(follow_redirects=True) as client:
        # делаем зпапрос на страницу авторизации
        response = client.get(LOGIN_PAGE_URL)
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
        login_response = client.post(LOGIN_ACTION_URL, files=form_fields, headers=headers)

        params = {
            "section": "audios",
            "q": "",
            "p": 1, 
        }
    
        # добавляем словарь чтобы удобно обращаться к адресу для скачивания файла по названию 
        tracks_urls = {}

        if track_container is not None:
            track_container.bind(ptg.keys.UP, lambda *_: track_container.scroll(-1))
            track_container.bind(ptg.keys.DOWN, lambda *_: track_container.scroll(1))
            track_container.bind(ptg.keys.PAGE_UP, lambda *_: track_container.scroll(-10))
            track_container.bind(ptg.keys.PAGE_DOWN, lambda *_: track_container.scroll(10))

        while True:
            # запрос на страницу с музыкой и вывод статуса
            music_response = client.get(music_adr, params=params)
            music_soup = BeautifulSoup(music_response.text, "html.parser")

            # создаем проверку есть ли div поиска на сайте
            target_div = None
            #target_div = soup.select_one('#search_page .page_wrap_content_main')
            parent = music_soup.find('div', id='search_page')
        
            if parent:
                # ищем div с треками
                target_div = parent.find('div', class_='page_wrap_content_main')
        
                if target_div:
                    #print(target_div.prettify())
                    audio_tracks = target_div.find_all('div', class_='scroll_node')
                
                    # создаем список треков и выводим
                    for track in audio_tracks:
                        # находим div с классом audioEmbed и выводим data-name(название трека с исполнителем) в консоль
                        audio_embed = track.find('div', class_="audioEmbed")
                    
                        if audio_embed:
                            #track_name = audio_embed.get('data-name')
                            #track_url = audio_embed.get('data-url')
                        
                            #tracks_urls[track_name] = track_url
                            #ui.music_list.append(ui.ptg.Button(track_name, lambda: download_and_play_with_mpv(track_urls[track_name])))
                            #download_and_play_with_mpv(tracks_urls[track_name])

                            name = audio_embed.get('data-name')
                            url = audio_embed.get('data-url')

                            track_url = url
                                
                            if name and url and ui.music_window:
                                #button = ptg.Button(name, lambda _: download_and_play(track_url))
                                #ui.music_window._widgets.append(button)
                                #ui.manager.compositor.draw()
                                #ui.manager.update() 
                                add_track_to_list(name, track_url)
                                time.sleep(0.05)

            # увелечиваем значение p чтобы загрузить новые треки и делаем паузу чтобы сервер не перетруждался
            params["p"] += 1
            time.sleep(1)

if __name__ == "__main__":
    ui.start_player()