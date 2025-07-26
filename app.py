from shiny import App, ui

app_ui = ui.page_fluid(
    ui.h2("Welcome to My Shiny App")  # Header (level 2)
)

def server(input, output, session):
    pass  # No server-side logic needed

app = App(app_ui, server)
