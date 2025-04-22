from tqdm import tqdm

def apply_bottom_zones(df, rolling_window=60):
    df['is_bottom'] = (
        (df['mid_l'] == df['mid_l'].rolling(window=rolling_window).min())
    )

