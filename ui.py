from textual import on
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Footer, Input, Label, ListItem, ListView
from textual.widgets import ListView  # Убедимся, что импорт есть

login_email = ""
login_password = ""

class LoginScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Авторизация LainPlayer", id="title")
        yield Input(placeholder="Email", id="email_input")
        yield Input(placeholder="Пароль", password=True, id="password_input")
        yield Button("Войти", variant="success", id="login_btn")

    @on(Button.Pressed, "#login_btn")
    def do_login(self) -> None:
        email = self.query_one("#email_input", Input).value
        password = self.query_one("#password_input", Input).value
        
        self.app.save_credentials(email, password)
        self.app.switch_screen(MainScreen())

class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        yield ListView(id="my_list")
        yield Footer()
    
    def on_mount(self) -> None:
        """Запускаем загрузку музыки после монтирования экрана"""
        if self.app.setup_worker:
            self.app.run_worker(self.app.setup_worker(self))
    
    def add_track(self, name: str, url: str) -> None:
        """Безопасно добавляет трек в список на этом экране"""
        try:
            list_view = self.query_one("#my_list", ListView)
            
            item = ListItem(Label(name))
            
            item.track_name = name
            item.track_url = url
            
            list_view.append(item)
            
        except Exception as e:
            self.app.notify(f"Ошибка добавления трека: {e}", severity="error")

class LainPlayerUI(App):
    def __init__(self, action_function=None, setup_worker=None):
        super().__init__()
        self.action_function = action_function
        self.setup_worker = setup_worker
    
    def on_mount(self) -> None:
        self.push_screen(LoginScreen())
    
    def save_credentials(self, email, password):
        global login_email, login_password
        login_email = email
        login_password = password
    
    @on(ListView.Selected, "#my_list")
    def on_select(self, event: ListView.Selected) -> None:
        if self.action_function:
            self.action_function(event.item, self)
