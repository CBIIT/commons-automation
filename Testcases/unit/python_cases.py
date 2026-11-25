"""Run a Python testcase against a recording app without starting a browser."""
from pathlib import Path
import runpy


def run_python_case(app, path):
    path = Path(path)
    if not hasattr(app, 'output_dir'):
        app.output_dir = Path('/evidence')
    namespace = runpy.run_path(str(path))
    namespace[path.stem](app)


def case_report_name(path):
    return Path(path).stem.removeprefix('test_')
