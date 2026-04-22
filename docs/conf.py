"""Sphinx configuration for asyoulikeit."""

from datetime import datetime
from importlib.metadata import version as get_version

# -- Project information -----------------------------------------------------

project = "asyoulikeit"
author = "Sixty North AS"
copyright = f"{datetime.now().year}, {author}"

# `release` is the full version string, `version` the short (major.minor).
release = get_version("asyoulikeit")
version = ".".join(release.split(".")[:2])


# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",       # Google / NumPy-style docstrings
    "sphinx.ext.viewcode",       # "[source]" links next to each documented object
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",         # copy-to-clipboard on code blocks
]

# Docstrings throughout the code use Google style.
napoleon_google_docstring = True
napoleon_numpy_docstring = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "click": ("https://click.palletsprojects.com/en/stable/", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_logo = "_static/logo.svg"
html_favicon = "_static/logo.png"

html_theme_options = {
    # The logo carries the wordmark, so don't repeat the project name below it.
    "logo_only": True,
}
