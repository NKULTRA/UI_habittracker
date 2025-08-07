"""
Main starting script for the application
"""
import os
from pathlib import Path

from shiny import App, ui, render, reactive
from modules import user_selection_module, home_screen_module, edit_habits_module, habit_analytics_module
from services.database import setup_database
from services.state import state

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
    
    ui.output_ui("main_ui")
)


def server(input, output, session):

    initialized_modules = set()

    @output
    @render.ui
    def main_ui():
        page = state()["current_page"]

        if page == "user_selection":
            return user_selection_module.user_selection_ui()
        elif page == "home_screen":
            return home_screen_module.home_screen_ui()
        elif page == "edit_habits":
            return edit_habits_module.edit_habits_ui()
        elif page == "analyze_habits":
            return habit_analytics_module.habit_analytics_ui()

    @reactive.Effect
    def run_server_logic():
        page = state()["current_page"]
        
        if page not in initialized_modules:
            if page == "user_selection":
                user_selection_module.user_selection_server(input, output, session)
            elif page == "home_screen":
                home_screen_module.home_screen_server(input, output, session)
            elif page == "edit_habits":
                edit_habits_module.edit_habits_server(input, output, session)
            elif page == "analyze_habits":
                habit_analytics_module.habit_analytics_server(input, output, session)
            initialized_modules.add(page)


app = App(app_ui, server, static_assets=static_path)
