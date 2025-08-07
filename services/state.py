from shiny import reactive

state = reactive.Value({
    "current_page": "user_selection",
    "current_user": None,
    "refresh_user": 0
})

def update_state(**kwargs):
    state.set({**state(), **kwargs})