# Desktop migration backup

`desktop_before_web_migration.zip` preserves the former Tkinter interface,
Canvas diagram, desktop launcher, GUI smoke check, requirements, and old README.
It was verified as a readable ZIP before obsolete desktop modules were removed.

The active project uses Flask and SVG. It no longer imports Tkinter or
CustomTkinter. The unchanged `core/` modules, original tests, grammar, and
laboratory data remain in the active project.

To study or restore the desktop version, extract this ZIP into a **separate
directory**, copy the active `core/`, `data/`, `tests/` (excluding `test_api.py`),
and `docs/grammar.md` there, then install the archived desktop requirements.
The former host-specific Tcl/Tk scripts are still in `artifacts/runtime/`;
a standard Python installation with Tcl/Tk support needs no such workaround.
Do not extract the desktop files over the migrated Flask application.
