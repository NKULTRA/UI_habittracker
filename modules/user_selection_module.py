"""
Module creates the first page of the application
The user selection screen
"""
from shiny import ui, reactive, render
from modules.home_screen_module import home_screen_ui, home_screen_server
from models.user import User
from services.database import user_exists


def user_selection_ui():
    """
    creates the user interface of the user selection screen
    """
    return ui.page_fluid(
        ui.div(
            {"class": "login-box"},

            ui.div(
                {"class": "inner-login-box"},
                ui.h3("Habit tracker"),
                ui.img(src="images/lifestyle.svg", class_="login-img"),
                ui.h3("Please click your name or create a new one"),
                ui.div(
                    {"class": "profile-container"},
                    ui.output_ui("user_tiles"),
                    ui.input_action_button("toggle_delete", "Toggle Delete Mode", class_="btn-danger")
                )
            )
        )
    )


def user_selection_server(input, output, session, current_page, current_user):
    
    delete_mode = reactive.Value(False)
    refresh_users = reactive.Value(0)

    @reactive.effect
    @reactive.event(input.toggle_delete)
    def _():
        delete_mode.set(not delete_mode())

    
    @output
    @render.ui
    def user_tiles():
        """
        function to render the user name tiles when there are already user in the database
        the create new user tile is always rendered
        """
        _ = refresh_users()
        tiles = []

        # add tiles for previously created users
        for user in User.get_all():
            style = "background-color: #f8d7da;" if delete_mode() else ""
            tiles.append(
                ui.div(
                    {"class": "profile-card", "id": f"user_{user.user_id}", "style": style},
                    ui.input_action_button(f"select_{user.user_id}", user.username)
                )
            )
        
        # new user input box
        tiles.append(
            ui.row(
                {"class": "new-user-card"},

                ui.column(8,
                          ui.input_text("create_user", None, placeholder="Create new user")
                ),

                ui.column(4,
                          ui.input_action_button("submit_new", "Create", disabled=True)
                )
            )
        )
        
        return tiles
    

    @reactive.Effect
    def toggle_button():
        """
        the create button next to the text input field is not clickable when there is no input yet
        this was set, because otherwise an empty string is written to the database
        """
        if input.create_user().strip():
            ui.update_action_button("submit_new", disabled=False)
        else:
            ui.update_action_button("submit_new", disabled=True)


    @reactive.Effect
    def handle_user_clicks():
        """
        reactive function to handle the user selection for already existing users
        - the user needs to click on one of the buttons with a name, after the current_user is set and the application
        switches to the home screen
        - because at application start it is not known how many buttons there will be, 
        this checks for all buttons and whether one was clicked, than breaks the loop
        """
        for user in User.get_all():
            btn = getattr(input, f"select_{user.user_id}")
            if btn() and btn() > 0:
                if delete_mode():
                    ui.modal_show(
                        ui.modal(
                            f"Are you sure you want to delete {user.username}?",
                            ui.input_action_button(f"confirm_delete_{user.user_id}", "Yes, delete", class_="btn-danger"),
                            ui.input_action_button("cancel_delete", "Cancel")
                        ),
                    )
                else:
                    current_user.set(user)
                    current_page.set("home_screen")
                    break   

    for user in User.get_all():
        @reactive.effect
        @reactive.event(getattr(input, f"confirm_delete_{user.user_id}"))
        def _(user=user):
            user.delete()
            delete_mode.set(False)
            refresh_users.set(refresh_users() + 1)
            ui.modal_remove()

    @reactive.effect
    @reactive.event(input.cancel_delete)
    def _():
        ui.modal_remove()

    @reactive.Effect
    @reactive.event(input.submit_new)
    def _():
        """
        reactive function to handle the user input in the textfield for 
        creating a new user
        - when the user already exists in the database, there is an error message
        - otherwise the user will be added to the database and the application goes to the home screen
        """
        name = input.create_user()

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
            current_user.set(new_user)
            current_page.set("home_screen")

