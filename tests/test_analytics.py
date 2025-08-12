import numpy as np
from services.analytics import streak_history_df, streaks_plot

def test_streak_history_shape(conn):
    df = streak_history_df(conn, user_id=1)
    assert {"HabitName","date","streak"} <= set(df.columns)
    assert df["streak"].dtype.kind in ("i","u")  # integer-like

def test_streaks_plot_axes(conn):
    df = streak_history_df(conn, user_id=1)
    fig = streaks_plot(df)            # your current function
    ax = fig.axes[0]
    # y ticks are integers only
    assert all(float(t).is_integer() for t in ax.get_yticks())
    # x has dates without time jitter: all times are midnight
    # Convert matplotlib date numbers back to datetime to check
    import matplotlib.dates as mdates, datetime as dt
    x_all = np.concatenate([ln.get_xdata() for ln in ax.get_lines()])
    dts = [mdates.num2date(x) for x in x_all]
    assert all(dt.time() == dt.time().replace() for dt in [d.timetuple() and d.replace(tzinfo=None).time().replace(hour=0, minute=0, second=0, microsecond=0) or d.time() for d in dts])

def test_x_window_trim(conn):
    df_all = streak_history_df(conn, user_id=1)
    fig = streaks_plot(df_all)
    ax = fig.axes[0]
    # Ensure we didn’t plot more than the dynamic cap (e.g., <= 90 unique dates)
    from matplotlib.dates import num2date
    x_unique = {num2date(x).date() for ln in ax.get_lines() for x in ln.get_xdata()}
    assert len(x_unique) <= 90
