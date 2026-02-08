# This file is part of vical.
# License: MIT (see LICENSE)

"""Shared mixins for classes that need access to editor, UI, or settings."""

class EditorAware:
    """Mixin to give access to the global editor object."""
    editor: "Editor" = None  # type hint for clarity

    @staticmethod
    def editor_set(editor):
        EditorAware.editor = editor


class UIAware:
    """Mixin to give access to the global UI object."""
    ui: "UI" = None

    @staticmethod
    def ui_set(ui):
        UIAware.ui = ui


class SettingsAware:
    """Mixin for classes that need both editor and UI access."""
    editor: "Editor" = None
    ui: "UI" = None

    @staticmethod
    def set_editor(editor):
        SettingsAware.editor = editor

    @staticmethod
    def set_ui(ui):
        SettingsAware.ui = ui
