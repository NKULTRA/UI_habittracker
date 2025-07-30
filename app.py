"""
Main starting script for the application

"""

from shiny import App, ui
from modules.home_screen_module import home_screen_ui, home_screen_server

app_ui = ui.page_fluid(
        
    ui.head_content(
        ui.include_css("static/styles.css")  # load custom styles
    ),
    
    home_screen_ui()
)

def server(input, output, session):
    home_screen_server(input, output, session)


app = App(home_screen_ui, home_screen_server)
