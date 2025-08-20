"""
Main starting script for the application
"""
from pathlib import Path

from shiny import App, ui, render, reactive
from modules import user_selection_module, home_screen_module, edit_habits_module, habit_analytics_module
from services.database import setup_database
from services.state import state

# sets up the database from services/database.py
setup_database()

dir = Path.cwd().resolve() # current working directory
static_path = dir.joinpath("static") # folder with images and the stylesheet


app_ui = ui.page_fluid(
    ui.head_content(
        ui.tags.link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/bootswatch@5.3.0/dist/lumen/bootstrap.min.css" # bootstrap style sheet
        ),
        ui.tags.link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Open+Sans&display=swap" # google open sans font
        ),
        ui.tags.link(rel="icon", type="image/png", href="images/fav_lifestyle.png"),
        ui.include_css("static/styles.css") # css styles in /static
    ),
    ui.output_ui("main_ui"),
    title="Habit Tracker"
)


def server(input, output, session):

    initialized_modules = set()
    _last_page = reactive.Value(None)

    @output
    @render.ui
    def main_ui():
        """
        handles the rendering of the page the user currently is
        """
        page = state()["current_page"]

        if page == "user_selection":
            return user_selection_module.user_selection_ui()
        elif page == "home_screen":
            return home_screen_module.home_screen_ui()
        elif page == "edit_habits":
            return edit_habits_module.edit_habits_ui()
        elif page == "analyze_habits":
            return habit_analytics_module.habit_analytics_ui()


    @reactive.effect
    def run_server_logic():
        """
        Mount the server() of the page the user navigated to
        """
        page = state()["current_page"]
        
        # only react when the current page actually changes, just to reduce reactivity
        if _last_page.get() == page:
            return
        _last_page.set(page)

        # mount server functions only once
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
