
from image_processing import compare_observations

first_path = "../data/wise0855_first_cutout.fits"
second_path = "../data/wise0855_second_cutout.fits"

result = compare_observations(
    first_path,
    second_path
)

print("\n" + "=" * 55)
print("SPHEREx IMAGE COMPARISON")
print("=" * 55)

print("Valid pixels:", result["valid_pixel_count"])

print(
    "Overlap:",
    f'{result["overlap_percentage"]:.2f}%'
)

print("Image unit:", result["unit"])

print(
    "First background:",
    result["first_background"]
)

print(
    "Second background:",
    result["second_background"]
)

print(
    "Background offset:",
    result["background_offset"]
)

print(
    "Difference median:",
    result["difference_median"]
)

print(
    "Difference standard deviation:",
    result["difference_std"]
)

print(
    "Sources in first image:",
    result["first_sources"]["number_of_sources"]
)

print(
    "Sources in second image:",
    result["second_sources"]["number_of_sources"]
)

print("\nComparison test completed.")
