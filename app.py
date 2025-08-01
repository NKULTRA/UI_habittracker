"""
Main starting script for the application

"""

from shiny import App, ui
from modules.user_selection_module import user_selection_ui, user_selection_server

app_ui = ui.page_fluid(
        
    ui.head_content(
        ui.include_css("static/styles.css")  # load custom styles
    ),
    
    user_selection_ui()
)

def server(input, output, session):
    user_selection_server(input, output, session)


app = App(app_ui, server)
