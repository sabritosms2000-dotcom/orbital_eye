
import pandas as pd

df = pd.read_csv("wise0855_corrected_results.csv")

# Convert observation times
df["observation_datetime"] = pd.to_datetime(
    df["observation_datetime"]
)

# Choose earliest and latest dates
earliest_date = df["observation_datetime"].dt.date.min()
latest_date = df["observation_datetime"].dt.date.max()

for label, date in [
    ("EARLIEST", earliest_date),
    ("LATEST", latest_date)
]:
    row = df[df["observation_datetime"].dt.date == date].iloc[0]

    base_url = "https://irsa.ipac.caltech.edu/" + row["uri"]
    cutout_url = (
        base_url
        + "?center=133.79513,-7.24515d&size=0.1"
    )

    print(f"\n===== {label} OBSERVATION =====")
    print("Date:", row["observation_datetime"])
    print("Plane ID:", row["planeid"])
    print("Band:", row["energy_bandpassname"])
    print("Cutout URL:", cutout_url)
