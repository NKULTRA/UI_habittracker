"""
Module creates the Edit Habits Screen 
after the user clicks the button on the home screen
"""
from shiny import ui, render


edit_habits_ui = ui.page_fluid(
    ui.h2("My modular shiny app"),
    ui.output_text("greeting")
)

def edit_habits_server(input, output, session):
    @output
    @render.text
    def greeting():
        return "Hello from server"