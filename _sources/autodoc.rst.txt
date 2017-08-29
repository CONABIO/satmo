Documentation
----------------

Package doc is built using Sphinx and hosted on a github gh-pages.
API doc is extracted from docstrings formatted according to the `Google Style Python Docstrings <http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html>`_


Building the doc
-----------------

To compile the documentation, checkout the ``gh-pages`` branch (``git checkout gh-pages`` if you already have a local copy of the branch, ``git checkout -b gh-pages origin/gh-pages`` otherwise), and run the ``compile-gh-doc.sh`` script.
Make sure all changes were commited before running that script; uncommited changes will be lost.
