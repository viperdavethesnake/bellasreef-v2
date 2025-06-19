import sys
import importlib

req_file = sys.argv[1]
missing = []

print("=== Requirements Module Check ===")
with open(req_file) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pkg = line.split("==")[0].replace("-", "_")  # pip names can have -, modules use _
        try:
            importlib.import_module(pkg)
            print(f"✔️  {pkg} imported successfully")
        except ImportError:
            print(f"❌  {pkg} MISSING or failed to import")
            missing.append(pkg)

if missing:
    print("\nWARNING: Some modules are missing or failed to import:")
    for m in missing:
        print(f"   - {m}")
    print("Try running: pip install -r <requirements.txt> again.")
else:
    print("\nAll modules imported successfully!")
