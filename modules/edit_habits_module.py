

edit_habits_ui = ui.page_fluid(
    ui.h2("My modular shiny app"),
    ui.output_text("greeting")
)

def edit_habits_server(input, output, session):
    @output
    @render.text
    def greeting():
        return "Hello from server"