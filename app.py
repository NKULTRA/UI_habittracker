from shiny import App
import sqlite3
from ui import app_ui
from server import app_server

app = App(app_ui, app_server)
