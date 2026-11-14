
import pandas as pd

df = pd.read_csv("../wise0855_corrected_results.csv")

print("CSV columns:")
print(df.columns.tolist())

print("\nD3 observations:")
d3 = df[df["energy_bandpassname"] == "SPHEREx-D3"]

print(
    d3[
        [
            "planeid",
            "time_bounds_lower",
            "observation_datetime",
            "uri"
        ]
    ].to_string(index=False)
)
