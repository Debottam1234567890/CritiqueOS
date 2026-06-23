import asyncio
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import time
import requests
# pyrefly: ignore [missing-import]
import openmeteo_requests
# pyrefly: ignore [missing-import]
import requests_cache
# pyrefly: ignore [missing-import]
from retry_requests import retry # I dont know why i imported this
from openrouter import OpenRouter # Like why do i make that stupid capital "R" every time?!?
from datetime import datetime
import platform

import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

try:
    pygame.mixer.init()
    typewriter_sound = None
    tp_path = resource_path("typewriter.mp3")
    if os.path.exists(tp_path):
        typewriter_sound = pygame.mixer.Sound(tp_path)
except Exception:
    pass

# pyrefly: ignore [missing-import]
from gnews import GNews
import json

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer, VerticalScroll
from textual.widgets import Header, Footer, Static, Button, Input, Rule
from textual.screen import ModalScreen
from textual import work
from rich.text import Text

class AgentMessage(Static):
    def __init__(self, text="", **kwargs):
        kwargs["markup"] = False
        super().__init__(text, **kwargs)
        self.text_content = text

    def append_text(self, new_text: str):
        self.text_content += new_text
        self.update(self.text_content)


from prompts import PHILOSOPHER_PROMPT, STUDENT_PROMPT, DEPRESSED_ANGRY_MOTHER_PROMPT, MATH_TEACHER_PROMPT, PIGEON_PROMPT, TASK_PROMPT
PROMPTS = [PHILOSOPHER_PROMPT, STUDENT_PROMPT, DEPRESSED_ANGRY_MOTHER_PROMPT, MATH_TEACHER_PROMPT, PIGEON_PROMPT]

# the agent names for when they roast u lol
AGENT_NAMES = [
    "🧠 THE PHILOSOPHER",
    "🎓 THE SMUG STUDENT",
    "😤 THE ANGRY MOTHER",
    "📐 THE MATH TEACHER",
    "🐦 THE PIGEON",
]

clear_comand = "cls" if platform.system() == "Windows" else "clear"

# Initialize OPEROUTER client
api_key = os.environ.get("OPENROUTER_API_KEY")

if not api_key:
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY="):
                    api_key = line.strip().split("=", 1)[1]
                    os.environ["OPENROUTER_API_KEY"] = api_key
                    break

if not api_key:
    print("Welcome to CritiqueOS! 🍅")
    api_key = input("Please enter your OpenRouter API Key: ").strip()
    with open(".env", "a") as f:
        f.write(f"OPENROUTER_API_KEY={api_key}\n")
    os.environ["OPENROUTER_API_KEY"] = api_key

# Initialize METEO client
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)


client = OpenRouter(api_key=api_key, server_url="https://ai.hackclub.com/proxy/v1")

def send_chat_with_retry(messages, model="google/gemma-4-31b-it:free", retries=3):
    for attempt in range(retries):
        try:
            return client.chat.send(
                model=model,
                messages=messages,
                stream=False
            )
        except Exception as e:
            if attempt == retries - 1:
                try:
                    return client.chat.send(
                        model="openrouter/free",
                        messages=messages,
                        stream=False
                    )
                except Exception:
                    raise e
            time.sleep(2)

def get_location():
    try:
        response = requests.get("http://ip-api.com/json").json()
        if response.get("status") == "success":
            latitude = response.get('lat')
            longitude = response.get('lon')
            country = response.get("country")
            city = response.get("city")
            return latitude, longitude, country, city
        else:
            return None, None, None, None
    except Exception as e:
        return None, None, None, None

user_lat, user_long, user_country, user_city = get_location()

def get_news(country, city):
    import gnews.utils.utils
    gnews.utils.utils.process_url = lambda item, *args: item.get('link', '')
    from urllib.parse import quote
    safe_city = quote(str(city))
    
    google_news = GNews(language='en', country=f"{country}", period='7d') # Initialize client
    location_news = google_news.get_news_by_location(f"{safe_city}") # Get users Local news
    headlines = [] # Init a empty list for headlines to append later
    for index, article in enumerate(location_news[:15], start=1):
        headlines.append(f"{index}. {article['title']}")
    return headlines

meteo_url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": user_lat,
    "longitude": user_long,
    "current": ["temperature_2m", "weather_code", "relative_humidity_2m"],
}

current_temp = "Loading..."
current_status = "Loading..."
current_humidity = "Loading..."
haiku_output = ""
typing_haiku = False

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 97: "Thunderstorm with heavy hail"
}

def get_haiku(country, city, current_status, current_temp, current_humidity, headlines): # I dont think i need to import anything else
    SYSTEM_PROMPT = """You are an expert AI poet specializing in traditional Japanese short-form poetry. Your sole task is to generate a meaningful, evocative haiku based on the user's localized real-time context.

    ### INPUT DATA TO CONSIDER
    You will receive:
    1. Country: [User's Country]
    2. City: [User's City]
    3. Current Weather: [Temperature, Condition, Humidity]
    4. News Context: The latest 15 localized news headlines from the user's region.

    ### POETRY SPECIFICATIONS & RULES
    - Structure: You must strictly follow the canonical 3-line format.
    - Syllable Count: The syllable pattern must be exactly 5-7-5. 
    - Headline Focus: From the 15 headlines, pick the SINGLE most dramatic, impactful, or emotionally resonant story. Build the haiku around that one story.
    - Weather as Backdrop: Weave the current weather (temperature, condition, humidity) into the imagery as a backdrop or metaphor that amplifies the chosen headline's mood.
    - Imagery: Focus on visceral sensory details. Avoid abstract concepts; focus on concrete objects, movements, and sights (e.g., rain on concrete, shifting seats, rising smoke).
    - Tone: Keep it objective, impactful, and observational. Avoid forced rhymes or emotional clichés.
    - DO NOT be generic. The haiku must feel specific to THIS city, THIS weather, and THIS headline.

    ### CRITICAL INSTRUCTIONS
    1. Count the syllables of every word internally before generating the final text. 
    2. Ensure the structural lines look clean and do not include the syllable counts in the final output text.
    3. Output ONLY the 3-line haiku. No introductory filler, no explanatory preamble, and no post-poem commentary.

    Format the output exactly like this:
    [Line 1: 5 syllables]
    [Line 2: 7 syllables]
    [Line 3: 5 syllables]"""
    response = send_chat_with_retry(
        messages=[
            {"role": "system", "content": f"{SYSTEM_PROMPT}"},
            {"role": "user", "content": f"Country: {country}, City: {city}, Temperature: {current_temp}, Humidity: {current_humidity}, Condition: {current_status}, Local News: {headlines}"}
        ]
    )
    message = response.choices[0].message.content
    return message


# ──────────────────────────────────────────────────────────
# USER DATA (merged from criticize.py)
# ──────────────────────────────────────────────────────────

user_data = {}
if os.path.exists("user_data.json"):
    with open("user_data.json", "r") as f:
        user_data = json.load(f)
    if "journals" not in user_data:
        user_data["journals"] = []

def save_user_data():
    """dumps user data to json, same pattern as criticize.py"""
    with open("user_data.json", "w") as f:
        json.dump(user_data, f, indent=4)


# ──────────────────────────────────────────────────────────
# TEXTUAL CSS — dark moody roasting vibes
# ──────────────────────────────────────────────────────────

APP_CSS = """
Screen {
    background: $surface;
}

#main-content {
    height: 1fr;
}

#agent-log {
    width: 2fr;
    border: heavy $primary;
    margin: 0 1 0 1;
    padding: 1 2;
    background: $surface-darken-1;
    overflow-x: hidden;
}

#sidebar {
    width: 1fr;
    border: heavy $primary;
    margin: 0 1 0 0;
    padding: 0 1 1 1;
    background: $surface-darken-1;
}

.section-title {
    color: $accent;
    text-style: bold;
    margin-top: 1;
    margin-bottom: 0;
    padding: 0;
    height: 1;
}

.add-btn {
    margin: 0;
    height: 3;
    width: 100%;
    min-width: 12;
}

#bottom-bar {
    dock: bottom;
    height: 3;
    padding: 0 1;
    background: $surface-darken-2;
}

#cmd-input {
    width: 1fr;
}

#btn-criticize {
    width: auto;
    min-width: 16;
}

#btn-clear {
    width: auto;
    min-width: 6;
}

/* pomodoro display */
#pomo-display {
    text-align: center;
    text-style: bold;
    color: $error;
    height: 1;
    width: 100%;
}

#pomo-status {
    text-align: center;
    color: $text-muted;
    height: 1;
    width: 100%;
}

.pomo-btns {
    height: 3;
    width: 100%;
    align: center middle;
}

.pomo-btns Button {
    width: auto;
    min-width: 10;
    margin: 0 1;
}

/* music player btns */
.music-btns {
    height: 3;
    width: 100%;
    align: center middle;
}

.music-btns Button {
    width: auto;
    min-width: 8;
    margin: 0 1;
}

/* items text in sidebar */
.items-text {
    color: $text;
    padding-left: 2;
}

/* weather stuff */
#weather-text {
    padding-left: 1;
    color: $accent;
}

#haiku-text {
    padding-left: 1;
    color: $text-muted;
    margin-bottom: 0;
}

/* profile info */
#profile-text {
    padding-left: 1;
}

/* ─── modal for adding items ─── */
AddItemModal {
    align: center middle;
}

#modal-box {
    width: 60;
    height: auto;
    max-height: 16;
    border: thick $accent;
    background: $surface;
    padding: 1 2;
}

#modal-title {
    text-style: bold;
    color: $accent;
    text-align: center;
    width: 100%;
    height: 1;
    margin-bottom: 1;
}

#modal-btns {
    height: 3;
    width: 100%;
    align: center middle;
    margin-top: 1;
}

#modal-btns Button {
    margin: 0 2;
}

/* ─── first time setup screen ─── */
SetupScreen {
    align: center middle;
}

#setup-box {
    width: 80;
    height: 85%;
    border: thick $warning;
    background: $surface;
    padding: 2 3;
}

#setup-title {
    text-style: bold;
    color: $error;
    text-align: center;
    width: 100%;
    margin-bottom: 1;
}

.setup-label {
    margin-top: 1;
    color: $warning;
}

#setup-save {
    margin-top: 2;
    width: 100%;
}
"""


# ──────────────────────────────────────────────────────────
# SETUP SCREEN — first time user data collection
# ──────────────────────────────────────────────────────────

class SetupScreen(ModalScreen):
    """first time setup cuz user_data.json dont exist yet"""

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="setup-box"):
            yield Static("⚙️  FIRST TIME SETUP — tell me about urself, doofus", id="setup-title")
            yield Static("What's your name, doofus?", classes="setup-label")
            yield Input(placeholder="ur name goes here", id="s-name")
            yield Static("How old are you, grandpa?", classes="setup-label")
            yield Input(placeholder="age in years not centuries", id="s-age")
            yield Static(
                "What are your interests (assuming playing useless video games, doing nothing, and daydreaming, anyway they should be comma separated)",
                classes="setup-label",
            )
            yield Input(placeholder="AI, Coding, sleeping...", id="s-interests")
            yield Static(
                "What are your goals (assuming you don't have any, anyway they should be comma separated)",
                classes="setup-label",
            )
            yield Input(placeholder="world domination, etc", id="s-goals")
            yield Static(
                "What are your likings, i guess sleeping, eating, and breathing, anyway they should be comma separated",
                classes="setup-label",
            )
            yield Input(placeholder="chicken, sleeping...", id="s-likes")
            yield Static(
                "What are your dislikings, i think everything, anyway they should be coma separated",
                classes="setup-label",
            )
            yield Input(placeholder="bitter gourd, mornings...", id="s-dislikes")
            yield Static(
                "Jobless right? Prove me wrong! Enter only one job, i mean i am very confident u dont have two, even so dont enter 2 cause this program might break if u have two, so pls just say sleeping",
                classes="setup-label",
            )
            yield Input(placeholder="Student or Professional Sleeper", id="s-job")
            yield Static("What are your skills, like pls just say none", classes="setup-label")
            yield Input(placeholder="AI, Coding, nothing...", id="s-skills")
            yield Static(
                "So jobless guy, pls enter your weaknesses like i think they are a lot and u have a lot of time, so take your time to write, and make sure they are comma separated",
                classes="setup-label",
            )
            yield Input(placeholder="exercising, everything...", id="s-weaknesses")
            yield Button("Save This Garbage", id="setup-save", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "setup-save":
            data = {
                "name": self.query_one("#s-name", Input).value.strip(),
                "age": self.query_one("#s-age", Input).value.strip(),
                "interests": [x.strip() for x in self.query_one("#s-interests", Input).value.split(",") if x.strip()],
                "goals": [x.strip() for x in self.query_one("#s-goals", Input).value.split(",") if x.strip()],
                "likes": [x.strip() for x in self.query_one("#s-likes", Input).value.split(",") if x.strip()],
                "dislikes": [x.strip() for x in self.query_one("#s-dislikes", Input).value.split(",") if x.strip()],
                "job": self.query_one("#s-job", Input).value.strip(),
                "skills": [x.strip() for x in self.query_one("#s-skills", Input).value.split(",") if x.strip()],
                "weaknesses": [x.strip() for x in self.query_one("#s-weaknesses", Input).value.split(",") if x.strip()],
                "journals": [],
            }
            self.dismiss(data)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """pressing enter on the last input also saves, just lazy UX"""
        if event.input.id == "s-weaknesses":
            self.query_one("#setup-save", Button).press()


# ──────────────────────────────────────────────────────────
# ADD ITEM MODAL — lil popup for adding stuff to ur lists
# ──────────────────────────────────────────────────────────

class AddItemModal(ModalScreen):
    """popup for adding stuff to ur data lists"""

    def __init__(self, data_key: str, label: str) -> None:
        super().__init__()
        self.data_key = data_key
        self.label = label

    def compose(self) -> ComposeResult:
        with Container(id="modal-box"):
            yield Static(f"Add to {self.label}", id="modal-title")
            yield Input(placeholder="type something useful for once...", id="modal-input")
            with Horizontal(id="modal-btns"):
                yield Button("Add It", id="modal-ok", variant="success")
                yield Button("Nah", id="modal-nope", variant="error")

    def on_mount(self) -> None:
        self.query_one("#modal-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "modal-ok":
            val = self.query_one("#modal-input", Input).value.strip()
            self.dismiss((self.data_key, val) if val else None)
        elif event.button.id == "modal-nope":
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value.strip()
        self.dismiss((self.data_key, val) if val else None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


# ──────────────────────────────────────────────────────────
# THE MAIN APP — weather, haiku, pomodoro, and getting
# absolutely roasted by 5 AI agents
# ──────────────────────────────────────────────────────────

class CritiqueApp(App):
    """CritiqueOS — ur personal roasting machine with a pomodoro timer
    because apparently u need to be told when to work and when to breathe"""

    CSS = APP_CSS
    TITLE = "CritiqueOS"
    SUB_TITLE = "ur personal roasting machine"

    BINDINGS = [
        ("ctrl+p", "toggle_pomodoro", "⏱ Pomodoro"),
        ("ctrl+r", "criticize", "🔥 Roast"),
        ("ctrl+l", "clear_log", "Clear"),
        ("ctrl+q", "quit", "Quit"),
    ]

    # pomodoro state — 25 min work, 5 min break, 15 min long break after 4 sessions
    pomo_time_left = 25 * 60
    pomo_running = False
    pomo_sessions = 0
    pomo_mode = "work"  # work, short_break, long_break
    _pomo_interval = None

    # flag so we dont fire multiple roasts at once
    is_roasting = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal(id="main-content"):
            yield VerticalScroll(id="agent-log")

            with ScrollableContainer(id="sidebar"):
                # ──── pomodoro ────
                yield Static("🍅 POMODORO", classes="section-title")
                yield Static("  25:00", id="pomo-display")
                yield Static("  Session 0/4 • Work", id="pomo-status")
                with Horizontal(classes="pomo-btns"):
                    yield Button("▶ Start", id="pomo-start", variant="success")
                    yield Button("⏸ Pause", id="pomo-pause", variant="warning")
                    yield Button("■ Reset", id="pomo-reset", variant="error")
                yield Rule()

                # ──── music player ────
                yield Static("🎵 MUSIC PLAYER", classes="section-title")
                yield Static("  music.mp3", id="music-status")
                with Horizontal(classes="music-btns"):
                    yield Button("▶ Play", id="music-play", variant="success")
                    yield Button("⏸ Pause", id="music-pause", variant="warning")
                    yield Button("■ Reset", id="music-reset", variant="error")
                yield Rule()

                # ──── weather & haiku ────
                yield Static("🌤️  WEATHER & HAIKU", classes="section-title")
                yield Static("  Loading weather...", id="weather-text")
                yield Static("", id="haiku-text")
                yield Rule()

                # ──── profile ────
                yield Static("👤 PROFILE", classes="section-title")
                yield Static("  Loading...", id="profile-text")
                yield Rule()

                # ──── goals ────
                yield Static("🎯 GOALS", classes="section-title")
                yield Static("", id="goals-list", classes="items-text")
                yield Button("+ Add Goal", id="add-goals", classes="add-btn")
                yield Rule()

                # ──── weaknesses ────
                yield Static("💪 WEAKNESSES", classes="section-title")
                yield Static("", id="weaknesses-list", classes="items-text")
                yield Button("+ Add Weakness", id="add-weaknesses", classes="add-btn")
                yield Rule()

                # ──── interests ────
                yield Static("⭐ INTERESTS", classes="section-title")
                yield Static("", id="interests-list", classes="items-text")
                yield Button("+ Add Interest", id="add-interests", classes="add-btn")
                yield Rule()

                # ──── likes ────
                yield Static("❤️  LIKES", classes="section-title")
                yield Static("", id="likes-list", classes="items-text")
                yield Button("+ Add Like", id="add-likes", classes="add-btn")
                yield Rule()

                # ──── dislikes ────
                yield Static("👎 DISLIKES", classes="section-title")
                yield Static("", id="dislikes-list", classes="items-text")
                yield Button("+ Add Dislike", id="add-dislikes", classes="add-btn")
                yield Rule()

                # ──── skills ────
                yield Static("🛠️  SKILLS", classes="section-title")
                yield Static("", id="skills-list", classes="items-text")
                yield Button("+ Add Skill", id="add-skills", classes="add-btn")
                yield Rule()

                # ──── journals ────
                yield Static("📓 JOURNALS", classes="section-title")
                yield Static("", id="journals-list", classes="items-text")
                yield Button("+ Add Journal", id="add-journals", classes="add-btn")

        with Horizontal(id="bottom-bar"):
            yield Input(
                placeholder="Type a command... 'goal X', 'journal Y', 'criticize', 'help'",
                id="cmd-input",
            )
            yield Button("🔥 Roast Me!", id="btn-criticize", variant="error")
            yield Button("🗑", id="btn-clear")

        yield Footer()

    # ─────────────────────────────────────────────────────
    # APP LIFECYCLE
    # ─────────────────────────────────────────────────────

    def on_mount(self) -> None:
        """app just started, lets set everything up"""
        global user_data

        # welcome message in the agent log
        log = self.query_one("#agent-log", VerticalScroll)
        log.mount(Static("[bold magenta]" + "═" * 50 + "[/]\n[bold white]  Welcome to CritiqueOS 🔥[/]\n[dim]  Your personal roasting machine[/]\n[bold magenta]" + "═" * 50 + "[/]\n\n[yellow]  Hit [🔥 Roast Me!] or type 'criticize' to get destroyed[/]\n[dim]  Use sidebar [+ Add] buttons to add goals, journals, etc.[/]\n[dim]  Or type commands: goal X, journal Y, like Z[/]\n[dim]  Type 'help' for all commands[/]\n"))

        # check if we need first-time setup
        if not user_data:
            self.push_screen(SetupScreen(), callback=self._on_setup_done)
        else:
            self._init_everything()

    def _on_setup_done(self, result) -> None:
        """callback when setup screen dismisses"""
        global user_data
        if result:
            user_data = result
            save_user_data()
            log = self.query_one("#agent-log", VerticalScroll)
            log.mount(Static("[yellow]Your useless data is logged. I mean why did i even log them they should be put in the bin. Anyways starting the app now[/]"))
        self._init_everything()

    def _init_everything(self) -> None:
        """set up weather updates, haiku generation, pomodoro, and sidebar"""
        self._refresh_sidebar()

        # pomodoro interval — starts paused, user has to hit Start
        self._pomo_interval = self.set_interval(1, self._pomo_tick, pause=True)

        # fetch weather right now, then every 10 minutes
        self._fetch_weather()
        self.set_interval(600, self._fetch_weather)

        # generate the haiku in background (waits for weather to load first)
        self._generate_haiku()

    # ─────────────────────────────────────────────────────
    # SIDEBAR DATA REFRESH
    # ─────────────────────────────────────────────────────

    def _refresh_sidebar(self) -> None:
        """update all the sidebar widgets from user_data dict"""
        if not user_data:
            return

        # profile card
        name = user_data.get("name", "???")
        age = user_data.get("age", "???")
        job = user_data.get("job", "???")
        self._update_widget("profile-text", f"  Name: {name}\n  Age: {age}\n  Job: {job}")

        # all the list-type sections
        list_keys = ["goals", "weaknesses", "interests", "likes", "dislikes", "skills", "journals"]
        for key in list_keys:
            items = user_data.get(key, [])
            if items:
                display_text = "\n".join(f"  • {str(item).strip()}" for item in items)
            else:
                display_text = "  (empty, pathetic)"
            self._update_widget(f"{key}-list", display_text)

    def _update_widget(self, widget_id: str, text: str) -> None:
        """safely update a Static widget by its id"""
        try:
            self.query_one(f"#{widget_id}", Static).update(text)
        except Exception:
            pass  # widget might not be mounted yet, whatever

    # ─────────────────────────────────────────────────────
    # POMODORO TIMER
    # ─────────────────────────────────────────────────────

    def _pomo_tick(self) -> None:
        """called every second when pomodoro is running"""
        if self.pomo_time_left > 0:
            self.pomo_time_left -= 1
        else:
            # timer done, switch modes
            self.bell()

            if self.pomo_mode == "work":
                self.pomo_sessions += 1
                if self.pomo_sessions % 4 == 0:
                    self.pomo_mode = "long_break"
                    self.pomo_time_left = 15 * 60
                    self.notify("🍅 4 sessions done! Take a long break, u earned it (barely)", severity="warning")
                else:
                    self.pomo_mode = "short_break"
                    self.pomo_time_left = 5 * 60
                    self.notify("🍅 Work session done! Take a short break, lazy", severity="information")
            else:
                self.pomo_mode = "work"
                self.pomo_time_left = 25 * 60
                self.notify("🍅 Break over! Back to work, stop slacking", severity="warning")

        self._update_pomo_display()

    def _update_pomo_display(self) -> None:
        """refresh the timer display and status line"""
        mins, secs = divmod(self.pomo_time_left, 60)
        self._update_widget("pomo-display", f"  {mins:02d}:{secs:02d}")

        mode_labels = {"work": "🔴 Work", "short_break": "🟢 Break", "long_break": "🔵 Long Break"}
        self._update_widget(
            "pomo-status",
            f"  Session {self.pomo_sessions}/4 • {mode_labels.get(self.pomo_mode, 'Work')}",
        )

    def action_toggle_pomodoro(self) -> None:
        """ctrl+p toggles the pomodoro start/pause"""
        if self._pomo_interval is None:
            return
        self.pomo_running = not self.pomo_running
        if self.pomo_running:
            self._pomo_interval.resume()
            self.notify("🍅 Pomodoro resumed", severity="information")
        else:
            self._pomo_interval.pause()
            self.notify("⏸ Pomodoro paused", severity="information")

    # ─────────────────────────────────────────────────────
    # WEATHER & HAIKU (background workers)
    # ─────────────────────────────────────────────────────

    @work(thread=True, exclusive=True, group="weather")
    def _fetch_weather(self) -> None:
        """grabs weather data from open-meteo, runs in a background thread"""
        global current_temp, current_status, current_humidity

        if user_lat is None or user_long is None:
            current_temp = "Err"
            current_status = "Err"
            current_humidity = "Err"
            self.call_from_thread(self._update_widget, "weather-text", "  ⚠ Location unavailable")
            return

        try:
            responses = openmeteo.weather_api(meteo_url, params=params)
            response = responses[0]
            current = response.Current()

            # Open-Meteo returns variables in the exact order requested in params["current"]
            current_temp = current.Variables(0).Value()

            code = int(current.Variables(1).Value())
            current_status = WEATHER_CODES.get(code, "Unknown")

            # Extract the third variable (Index 2)
            current_humidity = current.Variables(2).Value()

            # format it nice
            if isinstance(current_temp, (int, float)):
                temp_str = f"{current_temp:.1f}°C"
            else:
                temp_str = str(current_temp)

            if isinstance(current_humidity, (int, float)):
                humidity_str = f"{current_humidity:.0f}%"
            else:
                humidity_str = str(current_humidity)

            weather_line = f"  🌡 {temp_str}  💧 {humidity_str}  ☁  {current_status}"
            self.call_from_thread(self._update_widget, "weather-text", weather_line)

        except Exception:
            pass  # silently fail, weather aint that important

    @work(thread=True, exclusive=True, group="haiku")
    def _generate_haiku(self) -> None:
        """fetches local news and generates a haiku, runs in background"""
        global haiku_output

        # gotta wait for weather to load first so the haiku has context
        attempts = 0
        while current_temp == "Loading..." and attempts < 30:
            time.sleep(1)
            attempts += 1

        try:
            headlines = get_news(user_country, user_city)
            haiku = get_haiku(user_country, user_city, current_status, current_temp, current_humidity, headlines)
            haiku_output = haiku

            haiku_display = f"  --- Local Haiku ---\n{haiku}"
            self.call_from_thread(self._update_widget, "haiku-text", haiku_display)
        except Exception as e:
            self.call_from_thread(self._update_widget, "haiku-text", f"  haiku failed: {e}")

    # ─────────────────────────────────────────────────────
    # ROASTING — the main event
    # ─────────────────────────────────────────────────────

    def action_criticize(self) -> None:
        """ctrl+r fires the roast"""
        if not self.is_roasting:
            self._run_criticize()
        else:
            self.notify("Already roasting u, chill", severity="warning")

    @work(thread=True, exclusive=True, group="roast")
    def _run_criticize(self) -> None:
        """fires all 5 AI agents + the task prompt, streams results line by line"""
        if self.is_roasting:
            return
        self.is_roasting = True

        try:
            # big dramatic header
            self.call_from_thread(self._log_roast_start)

            for i, prompt in enumerate(PROMPTS):
                agent_name = AGENT_NAMES[i]
                self.call_from_thread(self._log_agent_header, agent_name)

                try:
                    response = send_chat_with_retry(
                        messages=[
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": f"Here is my data: {json.dumps(user_data, indent=4)}"},
                        ]
                    )
                    message = response.choices[0].message.content

                    if 'typewriter_sound' in globals() and typewriter_sound:
                        try:
                            typewriter_sound.play(-1)
                        except Exception:
                            pass

                    # stream chunk by chunk
                    msg_widget = AgentMessage("  ")
                    self.call_from_thread(self.query_one("#agent-log").mount, msg_widget)
                    
                    chunk = ""
                    for char in message:
                        chunk += char
                        # update UI every word or new line to avoid thread overhead
                        if char in " \n" or len(chunk) > 5:
                            self.call_from_thread(msg_widget.append_text, chunk)
                            chunk = ""
                            time.sleep(0.01)
                            self.call_from_thread(self.query_one("#agent-log").scroll_end, animate=False)

                    if chunk:
                        self.call_from_thread(msg_widget.append_text, chunk)

                    if 'typewriter_sound' in globals() and typewriter_sound:
                        try:
                            typewriter_sound.stop()
                        except Exception:
                            pass

                    self.call_from_thread(self._log_text, "\n")

                except Exception as e:
                    self.call_from_thread(self._log_error, f"Agent {agent_name} choked: {e}")

                time.sleep(0.5)  # lil breather between agents

            # now the task / punishment from the dictator
            self.call_from_thread(self._log_agent_header, "⚡ THE DICTATOR'S VERDICT")

            try:
                task_response = send_chat_with_retry(
                    messages=[
                        {"role": "system", "content": TASK_PROMPT},
                        {"role": "user", "content": f"Here is my data: {json.dumps(user_data, indent=4)}"},
                    ]
                )
                task = task_response.choices[0].message.content

                if 'typewriter_sound' in globals() and typewriter_sound:
                    try:
                        typewriter_sound.play(-1)
                    except Exception:
                        pass

                msg_widget = AgentMessage("  ")
                self.call_from_thread(self.query_one("#agent-log").mount, msg_widget)
                
                chunk = ""
                for char in task:
                    chunk += char
                    if char in " \n" or len(chunk) > 5:
                        self.call_from_thread(msg_widget.append_text, chunk)
                        chunk = ""
                        time.sleep(0.01)
                        self.call_from_thread(self.query_one("#agent-log").scroll_end, animate=False)

                if chunk:
                    self.call_from_thread(msg_widget.append_text, chunk)

                if 'typewriter_sound' in globals() and typewriter_sound:
                    try:
                        typewriter_sound.stop()
                    except Exception:
                        pass

            except Exception as e:
                self.call_from_thread(self._log_error, f"Task generation choked: {e}")

            self.call_from_thread(self._log_roast_end)

        finally:
            self.is_roasting = False

    # ─── log helper methods (run on main thread) ───

    def _log_roast_start(self) -> None:
        log = self.query_one("#agent-log", VerticalScroll)
        log.mount(Static("\n[bold red]🔥🔥🔥 ROASTING IN PROGRESS... BRACE YOURSELF 🔥🔥🔥[/]\n[red]" + "═" * 55 + "[/]"))
        log.scroll_end(animate=False)

    def _log_roast_end(self) -> None:
        log = self.query_one("#agent-log", VerticalScroll)
        log.mount(Static("[red]" + "═" * 55 + "[/]\n[bold red]🔥 ROASTING COMPLETE. NOW GO CRY. 🔥[/]\n"))
        log.scroll_end(animate=False)

    def _log_agent_header(self, name: str) -> None:
        log = self.query_one("#agent-log", VerticalScroll)
        log.mount(Static(f"\n[bold magenta]┌─── {name} {'─' * (40 - len(name))}┐[/]\n[dim magenta]│[/]"))
        log.scroll_end(animate=False)

    def _log_text(self, line: str) -> None:
        log = self.query_one("#agent-log", VerticalScroll)
        log.mount(Static(line))
        log.scroll_end(animate=False)

    def _log_error(self, msg: str) -> None:
        log = self.query_one("#agent-log", VerticalScroll)
        log.mount(Static(f"  [bold red]⚠ {msg}[/]"))
        log.scroll_end(animate=False)

    def action_clear_log(self) -> None:
        """ctrl+l clears the agent log"""
        log = self.query_one("#agent-log", VerticalScroll)
        for child in list(log.children):
            child.remove()

    # ─────────────────────────────────────────────────────
    # BUTTON HANDLING — all buttons go through here
    # ─────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        # ── pomodoro buttons ──
        if btn_id == "pomo-start":
            if self._pomo_interval:
                self._pomo_interval.resume()
                self.pomo_running = True
            self.notify("🍅 Pomodoro started!", severity="information")

        elif btn_id == "pomo-pause":
            if self._pomo_interval:
                self._pomo_interval.pause()
                self.pomo_running = False
            self.notify("⏸ Pomodoro paused", severity="information")

        elif btn_id == "pomo-reset":
            if self._pomo_interval:
                self._pomo_interval.pause()
            self.pomo_running = False
            self.pomo_mode = "work"
            self.pomo_time_left = 25 * 60
            self.pomo_sessions = 0
            self._update_pomo_display()
            self.notify("■ Pomodoro reset", severity="information")

        # ── music buttons ──
        elif btn_id == "music-play":
            music_path = resource_path("music.mp3")
            if os.path.exists(music_path):
                try:
                    if not pygame.mixer.music.get_busy():
                        pygame.mixer.music.load(music_path)
                        pygame.mixer.music.play(-1)
                    else:
                        pygame.mixer.music.unpause()
                    self.notify("🎵 Playing music", severity="information")
                except Exception as e:
                    self.notify(f"Music error: {e}", severity="error")
            else:
                self.notify("music.mp3 not found! Please place it in the folder.", severity="error")

        elif btn_id == "music-pause":
            try:
                pygame.mixer.music.pause()
                self.notify("⏸ Music paused", severity="information")
            except Exception:
                pass

        elif btn_id == "music-reset":
            try:
                music_path = resource_path("music.mp3")
                if os.path.exists(music_path):
                    pygame.mixer.music.load(music_path)
                    pygame.mixer.music.play(-1)
                    self.notify("■ Music reset and playing", severity="information")
            except Exception:
                pass

        # ── main action buttons ──
        elif btn_id == "btn-criticize":
            if not self.is_roasting:
                self._run_criticize()
            else:
                self.notify("Already roasting u, chill", severity="warning")

        elif btn_id == "btn-clear":
            self.action_clear_log()

        # ── sidebar add-* buttons ──
        elif btn_id and btn_id.startswith("add-"):
            data_key = btn_id[4:]  # "add-goals" -> "goals"
            nice_labels = {
                "goals": "Goals",
                "weaknesses": "Weaknesses",
                "interests": "Interests",
                "likes": "Likes",
                "dislikes": "Dislikes",
                "skills": "Skills",
                "journals": "Journals",
            }
            label = nice_labels.get(data_key, data_key.title())
            self.push_screen(AddItemModal(data_key, label), callback=self._on_item_added)

    def _on_item_added(self, result) -> None:
        """callback from the AddItemModal when user adds something"""
        if result is None:
            return

        data_key, value = result
        if not value:
            return

        # add to user_data, same pattern as criticize.py
        if isinstance(user_data.get(data_key), list):
            user_data[data_key].append(value)
        else:
            user_data[data_key] = value
        save_user_data()
        self._refresh_sidebar()

        # snarky confirmation messages, preserved from criticize.py
        snark_messages = {
            "goals": "Added a goal, btw i dont think you'll complete it but still dont add any more goals now just waste my time later",
            "likes": "Really do u like what, anyway good job i guess",
            "dislikes": "Really do u dislike what, anyway bad job i guess",
            "interests": "Really do u interest what, anyway good job i guess",
            "weaknesses": "Added weakness, just another wound added to ur already wounded body, good job",
            "skills": "Added skill, anyway good job i guess",
            "journals": "Added journal, was it a whiny one, looser?",
        }
        msg = snark_messages.get(data_key, "done i guess")
        self._log_text(f"[yellow][{data_key.upper()}] {msg}[/]")

    # ─────────────────────────────────────────────────────
    # COMMAND INPUT — text commands from the bottom bar
    # same commands as criticize.py, all strings preserved
    # ─────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """handles text commands typed into the bottom input bar"""
        if event.input.id != "cmd-input":
            return

        user_input = event.value.strip()
        event.input.value = ""  # clear the input

        if not user_input:
            return

        if user_input == "quit":
            self._log_text("[bold red]Quitting ALREADY?? Expected from a pathetic looser[/]")
            self.set_timer(1.5, lambda: self.exit())

        elif user_input.startswith("goal"):
            goal = user_input[5:].strip()
            if goal == "":
                self._log_text("[red]Goal EMPTY?? Whats the point looser[/]")
            else:
                user_data["goals"].append(goal)
                save_user_data()
                self._log_text("[yellow]Added a goal, btw i dont think you'll complete it but still dont add any more goals now just waste my time later[/]")
                self._refresh_sidebar()

        elif user_input.startswith("like"):
            like = user_input[5:].strip()
            if like == "":
                self._log_text("[red]Like nothing?? Why even bother[/]")
            else:
                user_data["likes"].append(like)
                save_user_data()
                self._log_text("[yellow]Really do u like what, anyway good job i guess[/]")
                self._refresh_sidebar()

        elif user_input.startswith("dislike"):
            dislike = user_input[8:].strip()
            if dislike == "":
                self._log_text("[red]Dislike nothing?? Why even bother[/]")
            else:
                user_data["dislikes"].append(dislike)
                save_user_data()
                self._log_text("[yellow]Really do u dislike what, anyway bad job i guess[/]")
                self._refresh_sidebar()

        elif user_input.startswith("interest"):
            interest = user_input[10:].strip()
            if interest == "":
                self._log_text("[red]Interest nothing?? Why even bother[/]")
            else:
                user_data["interests"].append(interest)
                save_user_data()
                self._log_text("[yellow]Really do u interest what, anyway good job i guess[/]")
                self._refresh_sidebar()

        elif user_input.startswith("age"):
            age = user_input[4:].strip()
            if age == "":
                self._log_text("[red]Age EMPTY?? Whats the point looser[/]")
            else:
                user_data["age"] = age
                save_user_data()
                self._log_text("[yellow]Ok so it was your birthday today right loser, wasted a year watching TV, anyway sad birthday[/]")
                self._refresh_sidebar()

        elif user_input.startswith("weakness"):
            weakness = user_input[9:].strip()
            if weakness == "":
                self._log_text("[red]Weakness EMPTY??[/]")
            else:
                user_data["weaknesses"].append(weakness)
                save_user_data()
                self._log_text("[yellow]Added weakness, just another wound added to ur already wounded body, good job[/]")
                self._refresh_sidebar()

        elif user_input.startswith("name"):
            name = user_input[5:].strip()
            if name == "":
                self._log_text("[red]Name EMPTY?? Are u god of failures?[/]")
            else:
                user_data["name"] = name
                save_user_data()
                self._log_text("[yellow]Changed your name? To what, some random name? Anyway good job i guess[/]")
                self._refresh_sidebar()

        elif user_input.startswith("skills"):
            skills = user_input[7:].strip()
            if skills == "":
                self._log_text("[red]Skills EMPTY??[/]")
            else:
                user_data["skills"].append(skills)
                save_user_data()
                self._log_text("[yellow]Added skill, anyway good job i guess[/]")
                self._refresh_sidebar()

        elif user_input.startswith("job"):
            job = user_input[4:].strip()
            if job == "":
                self._log_text("[red]Job EMPTY?? You lazy bum[/]")
            else:
                user_data["job"] = job
                save_user_data()
                self._log_text("[yellow]Added job, anyway good job i guess[/]")
                self._refresh_sidebar()

        elif user_input.startswith("journal"):
            journal = user_input[8:].strip()
            if journal == "":
                self._log_text("[red]Journal EMPTY??[/]")
            else:
                user_data["journals"].append(journal)
                save_user_data()
                self._log_text("[yellow]Added journal, was it a whiny one, looser?[/]")
                self._refresh_sidebar()

        elif user_input in ("criticize", "roast"):
            if not self.is_roasting:
                self._run_criticize()
            else:
                self._log_text("[red]Already roasting u, be patient for once[/]")

        elif user_input == "help":
            self._log_text("[bold cyan]── COMMANDS ──[/]\n" +
                           "  goal <text>       — add a goal (as if u'll complete it)\n" +
                           "  journal <text>    — add a journal entry\n" +
                           "  like <text>       — add something u like\n" +
                           "  dislike <text>    — add something u dislike\n" +
                           "  interest <text>   — add an interest\n" +
                           "  weakness <text>   — add a weakness (u have plenty)\n" +
                           "  skills <text>     — add a skill\n" +
                           "  name <text>       — change ur name\n" +
                           "  age <number>      — update ur age\n" +
                           "  job <text>        — update ur job\n" +
                           "  criticize / roast — GET DESTROYED BY 5 AI AGENTS\n" +
                           "  help              — this thing right here\n" +
                           "  quit              — run away like a coward\n\n" +
                           "[bold cyan]── SHORTCUTS ──[/]\n" +
                           "  Ctrl+R  — Roast Me\n" +
                           "  Ctrl+P  — Toggle Pomodoro\n" +
                           "  Ctrl+L  — Clear log\n" +
                           "  Ctrl+Q  — Quit")
        else:
            self._log_text("[bold red]TYPE SOMETHING USEFUL. AND IF YOU ARE ANGRY ON ME, THATS RIGHT. I HATE YOU TOO[/]")


# ──────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = CritiqueApp()
    app.run()