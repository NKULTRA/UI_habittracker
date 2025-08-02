"""
Module creates the first page of the application
The user selection screen
"""
from shiny import ui, reactive, render
from models.user import User


def user_selection_ui():
    return ui.page_fluid(
        ui.div(
            {"class": "login-box"},

            ui.div(
                {"class": "inner-login-box"},
                ui.img(src="images/lifestyle.svg", class_="login-img"),
                ui.h3("Please login"),
                ui.div(
                    {"class": "profile-container"},
                    ui.output_ui("user_tiles") 
                )
            )
        )
    )


def user_selection_server(input, output, session):
    @output
    @render.ui
    def user_tiles():
        tiles = []

        # add tiles for previously created users
        for user in User.get_all():
            tiles.append(
                ui.div(
                    {"class": "profile-card", "id": f"user_{user.user_id}"},
                    ui.input_action_button(f"select_{user.user_id}", user.username)
                )
            )
        
        # new user input box
        tiles.append(
            ui.div(
                {"class": "profile-card", "id": "new_user"},
                ui.input_text("create_user", "New User"),
                ui.input_action_button("submit_new", "Create")
            )
        )
        
        return tiles
    

    @reactive.Effect
    @reactive.event(input.submit_new)
    def _():
        name = input.create_user()
        if name:
            User.create(name)
