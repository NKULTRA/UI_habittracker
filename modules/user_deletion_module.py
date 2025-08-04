from shiny import ui, reactive, render
from models.user import User
from services.state import update_state

def user_deletion_ui():
    return ui.page_fluid(
        ui.div(
            {"class": "login-box delete-mode"},
            ui.h3("Habit tracker - Delete User"),
            ui.img(src="images/lifestyle.svg", class_="login-img"),
            ui.h3("Click a user to delete"),

            # reactive list container
            ui.tags.ul({"class": "delete-list"}, ui.output_ui("delete_list")),

            ui.div(
                {"class": "profile-container"},
                ui.input_action_button("cancel_delete", "Cancel", class_="btn-secondary")
            )
        )
    )


def user_deletion_server(input, output, session):
    refresh_users = reactive.Value(0)  # controls re-rendering of the list

    @output
    @render.ui
    def delete_list():
        _ = refresh_users()  # re-run when updated
        items = []
        for user in User.get_all():
            # each user gets its own buttonless clickable item
            items.append(
                ui.tags.li(
                    {"class": "delete-item"},
                    ui.input_action_button(f"delete_{user.user_id}", user.username, class_="btn-danger list-btn")
                )
            )
        return items

    # register delete handlers
    @reactive.effect
    def register_delete_events():
        _ = refresh_users()
        for user in User.get_all():
            @reactive.effect
            @reactive.event(getattr(input, f"delete_{user.user_id}"), ignore_init=True)
            def _(uid=user.user_id, uname=user.username):
                ui.modal_show(
                    ui.modal(
                        f"Do you really want to delete '{uname}'?",
                        title="Confirm Deletion",
                        easy_close=True,
                        footer=ui.div(
                            ui.input_action_button(f"confirm_delete_{uid}", "Yes, Delete", class_="btn-danger"),
                            ui.modal_button("Cancel")
                        )
                    )
                )

                @reactive.effect
                @reactive.event(getattr(input, f"confirm_delete_{uid}"), ignore_init=True)
                def _():
                    User.get_by_id(uid).delete()
                    refresh_users.set(refresh_users() + 1)  # triggers list refresh
                    ui.modal_remove()

    # cancel goes back
    @reactive.effect
    @reactive.event(input.cancel_delete, ignore_init=True)
    def _():
        update_state(current_page="user_selection")
