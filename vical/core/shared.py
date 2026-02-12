# This file is part of vical.
# License: MIT (see LICENSE)

"""Shared mixins for classes that need access to editor or settings."""

class EditorAware:
    """Mixin to give access to the global editor object."""
    @staticmethod
    def editor_set(editor):
        EditorAware.editor = editor


class SettingsAware:
    """Mixin for classes that need both editor and UI access."""
    @staticmethod
    def settings_set(settings):
        SettingsAware.settings = settings