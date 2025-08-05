"""
Module creates the first page of the application
The user selection screen
"""
from shiny import ui, reactive, render
from models.user import User
from services.database import user_exists
from services.state import update_state

def user_selection_ui():
    """
    creates the user interface of the user selection screen
    """
    return ui.page_fluid(
        ui.div(
            {"class": "login-box"},
            ui.h3("Habit tracker"),
            ui.img(src="images/lifestyle.svg", class_="login-img"),
            ui.h3("Please click your name or create a new one"),

            ui.div(
                {"class": "profile-container"},
                ui.output_ui("user_tiles")
            ),

            ui.div( 
                {"class": "new-user-container"},
                ui.input_text("input_create", label=None, placeholder="Create new user"),
                ui.input_action_button("submit_new", "Create", disabled=True)
            )
        )
    )

def user_selection_server(input, output, session):

    refresh_user = reactive.Value(0)

    @output
    @render.ui
    def user_tiles():
        """
        function to render the user name tiles when there are already user in the database
        """
        tiles = []
        _ = refresh_user()

        # add tiles for previously created users
        for user in User.get_all():
            tiles.append(
                ui.div(
                    {"class": "profile-card", "id": f"user_{user.user_id}"},
                    ui.input_action_button(f"select_{user.user_id}", user.username)
                )
            )
                
        return tiles
    

    @reactive.effect
    def toggle_button():
        """
        the create button next to the text input field is not clickable when there is no input yet
        this was set, because otherwise an empty string can be written to the database
        """
        if input.input_create().strip():
            ui.update_action_button("submit_new", disabled=False)
        else:
            ui.update_action_button("submit_new", disabled=True)


    @reactive.effect
    def handle_user_clicks():
        """
        reactive function to handle the user selection for already existing users
        - the user needs to click on one of the buttons with a name, after the current_user is set and the application
        switches to the home screen
        """
        _ = refresh_user()

        for user in User.get_all():
            @reactive.effect
            @reactive.event(getattr(input, f"select_{user.user_id}"), ignore_init=True)
            def _(user=user):
                update_state(current_user=user, current_page="home_screen")


    @reactive.effect
    @reactive.event(input.submit_new)
    def _():
        """
        reactive function to handle the user input in the textfield for 
        creating a new user
        - when the user already exists in the database, there is an error message
        - otherwise the user will be added to the database and the application goes to the home screen
        """
        name = input.input_create()

        if user_exists(name):
            
            ui.modal_show(
                ui.modal(
                    f"The username '{name}' already exists.",
                    title="Duplicate User",
                    easy_close=True,
                    footer=ui.modal_button("OK")
                )
            )
        else:
            new_user = User.create(name)
            refresh_user.set(refresh_user() + 1)
            update_state(current_user=new_user, current_page="home_screen")
