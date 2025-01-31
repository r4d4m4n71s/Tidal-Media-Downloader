import os
import sys

# Add the project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("Python path:", sys.path)
print("Current directory:", os.getcwd())
print("Added to path:", current_dir)

print("\nTrying to import custom_mapper directly...")
try:
    from tidal_dl.custom.custom_mapper import AudioMetadataUpdater
    print("Successfully imported AudioMetadataUpdater")
except ImportError as e:
    print(f"Import error: {str(e)}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"Other error: {type(e).__name__} - {str(e)}")
    import traceback
    traceback.print_exc()

print("\nListing directory contents:")
for root, dirs, files in os.walk(current_dir):
    level = root.replace(current_dir, '').count(os.sep)
    indent = ' ' * 4 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 4 * (level + 1)
    for f in files:
        print(f"{subindent}{f}")

print("\nDone")