from tqdm import tqdm

def apply_bottom_zones(df, rolling_window=60):
    df['is_bottom'] = (
        (df['mid_l'] == df['mid_l'].rolling(window=rolling_window).min()) &
        (df['in_downtrend'] == True)
    )

    df['zone'] = df.apply(
        lambda row: (row['mid_l'], row['mid_h']) if row['is_bottom'] else None,
        axis=1
    )

    df['zone'] = df['zone'].ffill()

