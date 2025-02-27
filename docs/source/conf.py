# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'oauth_client'
copyright = '2025, John Glauber'
author = 'John Glauber'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['myst_parser',
              'sphinx.ext.autodoc',
              'sphinx.ext.duration',
              'sphinx.ext.doctest',
              'sphinx.ext.autosummary']

templates_path = ['_templates']
exclude_patterns = []

source_suffix = {'.rst': 'restructuredtext', '.md': 'restructuredtext'}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
