from validation.target_registry import list_targets
for t in list_targets():
    print(f'{t["id"]}: {len(t["local_fits"])} FITS')