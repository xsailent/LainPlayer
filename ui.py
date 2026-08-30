import pytermgui as ptg
import os
import threading

columns, lines = os.get_terminal_size()

manager = None
music_window = None
login_window = None

def start_player():
    global manager, music_window, login_window

    with ptg.WindowManager() as mgr:
        manager = mgr

        #music_list.width = columns
        #music_list.height = lines

        #music_list.pos = (0, 0)
    
        email_field = ptg.InputField("Input here", prompt="Email: ")
        password_field = ptg.InputField("Input here", prompt="Password: ")

        login_data = (
            ptg.Window(
                "",
                email_field,
                password_field,
                "",
                ["Submit", lambda *_: do_login(email_field.value, password_field.value)],
                width=60,
                box="DOUBLE",
            )
            .set_title("[210 bold]LainPlayer login manager")
            .center()
        )
    
        manager.add(login_data)
        manager.run()

def do_login(email, password):
    global manager, login_window, music_window
    
    import main
    main.login_email = email
    main.login_password = password
    
    # Убираем окно логина
    if login_window and manager:
        manager.remove(login_window)

    track_container = ptg.Container(
        box="EMPTY_VERTICAL",
        height=lines - 6,
    )

    music_window = ptg.Window(
        "",
        ptg.Label("[bold]🎵 Music List[/bold]"),
        "",
        track_container,
        "",
        ptg.Container(
            ptg.Button("▲", lambda *_: track_container.scroll(-5)),  # Вверх на 5
            ptg.Button("▼", lambda *_: track_container.scroll(5)),   # Вниз на 5
            ptg.Button("⇑", lambda *_: track_container.scroll_end(0)),   # В начало
            ptg.Button("⇓", lambda *_: track_container.scroll_end(-1)),  # В конец
            box="EMPTY_HORIZONTAL",
        ),
        width=columns,
        height=lines,
        box="DOUBLE",
    ).set_title("LainPlayer")
    
    # Сохраняем контейнер в глобальной переменной для доступа из main
    main.track_container = track_container
    
    manager.add(music_window)
    
    # Запускаем загрузку в потоке
    threading.Thread(target=main.load_music, daemon=True).start()