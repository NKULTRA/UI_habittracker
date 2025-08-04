from shiny import reactive

state = reactive.Value({
    "current_page": "user_selection",
    "current_user": None
})

def update_state(**kwargs):
    state.set({**state(), **kwargs})