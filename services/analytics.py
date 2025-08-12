def streak_history_df(conn, user_id: int) -> pd.DataFrame:
    """
    Returns columns: HabitName, date (datetime64[ns]), streak (int)
    """
    # run your SQL or compose from models; return tidy DataFrame

def streaks_plot(df: pd.DataFrame):
    # your current plotting function (with integer y-ticks & no time on x)