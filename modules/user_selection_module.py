"""
Module creates the first page of the application
The user selection screen
"""


user_selection_ui = ui.page_fluid(
    ui.h2("My modular shiny app"),
    ui.output_text("greeting")
)

def user_selection_server(input, output, session):
    @output
    @render.text
    def greeting():
        return "Hello from server"