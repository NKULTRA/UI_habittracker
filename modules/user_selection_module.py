"""
Module creates the first page of the application
The user selection screen
"""
from shiny import render, ui, reactive
from services.database import get_users, new_user


def user_selection_ui():
    return ui.page_fluid(
        ui.div(
            {"class": "login-box"},
            ui.div(
                {"class": "inner-login"},
                ui.img(src="images/goal.svg", class_="logo_login"),
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
        users = get_users()
        tiles = []

        for user_id, username in users:
            tiles.append(
                ui.div(
                    {"class": "profile-card", "id": f"user_{user_id}"},
                    ui.input_action_button(f"select_{user_id}", username)
                )
            )
        
        # New User tile
        tiles.append(
            ui.div(
                {"class": "profile-card", "id": "new_user"},
                ui.input_text("create_user", "New User")
            )
        )
    
        return tiles