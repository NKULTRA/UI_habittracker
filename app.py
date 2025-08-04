"""
Main starting script for the application
"""
import os
from pathlib import Path

from shiny import App, ui, render
from modules import user_selection_module, user_deletion_module, home_screen_module, edit_habits_module, habit_analytics_module
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


    @output
    @render.ui
    def main_ui():

        if state()["current_page"] == "user_selection":
            return user_selection_module.user_selection_ui()
        elif state()["current_page"] == "delete_screen":
            return user_deletion_module.user_deletion_ui()
        elif state()["current_page"] == "home_screen":
            return home_screen_module.home_screen_ui()
        elif state()["current_page"] == "edit_habits":
            return edit_habits_module.edit_habits_ui()
        elif state()["current_page"] == "analyze_habits":
            return habit_analytics_module.habit_analytics_ui()
        

    user_selection_module.user_selection_server(input, output, session)
    user_deletion_module.user_deletion_server(input, output, session)
    home_screen_module.home_screen_server(input, output, session)
    edit_habits_module.edit_habits_server(input, output, session)
    habit_analytics_module.habit_analytics_server(input, output, session)

app = App(app_ui, server, static_assets=static_path)
