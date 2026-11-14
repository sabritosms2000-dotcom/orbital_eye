
import pandas as pd
from astropy.time import Time

df = pd.read_csv("wise0855_tap_results.csv")

# Convert Modified Julian Date (MJD) to real dates
mjd_values = df["time_bounds_lower"].dropna().astype(float).values

times = Time(mjd_values, format="mjd", scale="utc")

df["observation_datetime"] = times.to_datetime()

print("===== WISE 0855 OBSERVATION DATES =====")

print("Total results:", len(df))
print("Unique plane IDs:", df["planeid"].nunique())

print("\nFirst 15 observation dates:")
print(df[["planeid", "observation_datetime",
          "energy_bandpassname"]].head(15).to_string(index=False))

print("\n===== DATE SUMMARY =====")

unique_dates = sorted(
    df["observation_datetime"].dt.date.unique()
)

print("Number of different observation dates:", len(unique_dates))

for date in unique_dates:
    print(date)

print("\nEarliest observation:",
      df["observation_datetime"].min())

print("Latest observation:",
      df["observation_datetime"].max())

print("\n===== BAND SUMMARY =====")
print(df["energy_bandpassname"].value_counts())

# Save corrected results
df.to_csv("wise0855_corrected_results.csv", index=False)

print("\nSaved: wise0855_corrected_results.csv")
print("===== ANALYSIS COMPLETE =====")
