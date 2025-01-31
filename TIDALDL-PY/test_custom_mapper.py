import os
import sys
import importlib.util
import traceback

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

print(f"Project directory: {project_dir}")
print("Python path:")
for p in sys.path:
    print(f"  {p}")

print("\nChecking module paths:")
module_paths = [
    os.path.join(project_dir, 'tidal_dl', '__init__.py'),
    os.path.join(project_dir, 'tidal_dl', 'custom', '__init__.py'),
    os.path.join(project_dir, 'tidal_dl', 'custom', 'custom_mapper.py')
]

for path in module_paths:
    print(f"{path} exists: {os.path.exists(path)}")

print("\nTrying to import modules directly:")
try:
    print("\nImporting tidal_dl.__init__")
    spec = importlib.util.spec_from_file_location("tidal_dl", module_paths[0])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print("Successfully imported tidal_dl.__init__")
except Exception as e:
    print(f"Error importing tidal_dl.__init__: {type(e).__name__} - {str(e)}")
    traceback.print_exc()

try:
    print("\nImporting tidal_dl.custom.__init__")
    spec = importlib.util.spec_from_file_location("tidal_dl.custom", module_paths[1])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print("Successfully imported tidal_dl.custom.__init__")
except Exception as e:
    print(f"Error importing tidal_dl.custom.__init__: {type(e).__name__} - {str(e)}")
    traceback.print_exc()

try:
    print("\nImporting tidal_dl.custom.custom_mapper")
    spec = importlib.util.spec_from_file_location("tidal_dl.custom.custom_mapper", module_paths[2])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print("Successfully imported tidal_dl.custom.custom_mapper")
except Exception as e:
    print(f"Error importing tidal_dl.custom.custom_mapper: {type(e).__name__} - {str(e)}")
    traceback.print_exc()

print("\nDone")