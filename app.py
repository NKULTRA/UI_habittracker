"""
Main starting script for the application
"""
import os
from pathlib import Path

from shiny import App, render, ui
from modules.user_selection_module import user_selection_ui, user_selection_server
from services.database import setup_database

setup_database()

dir = Path(os.path.abspath('')).resolve()
static_path = dir.joinpath("static")


app_ui = ui.page_fluid(
    ui.head_content(
        ui.tags.link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/bootswatch@5.3.0/dist/lumen/bootstrap.min.css"
        ),
        ui.tags.link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Open+Sans&display=swap"
        ),
        ui.include_css("static/styles.css")
    ),
    user_selection_ui() 
)


def server(input, output, session):
    user_selection_server(input, output, session) 


app = App(app_ui, server, static_assets=static_path)
