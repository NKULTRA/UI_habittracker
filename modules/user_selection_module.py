"""
Module creates the first page of the application
The user selection screen
"""
from shiny import render, ui


def user_selection_ui():
    return ui.page_fluid(
        ui.div(
            {"class": "login-box"},
            ui.div(
                {"class": "inner-login"},
                ui.img(src="images/goal.svg", class_="logo_login"),
                ui.h3("Please login"),
                ui.p("input_list")
            )
        )
    )


def user_selection_server(input, output, session):
    pass