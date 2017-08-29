#!/usr/bin/env bash

# Remove everything except this script
find . -type f -not -name 'compile-gh-doc.sh' -not -path '*/\.*' -print0 | xargs -0 rm --
# Checkout whatever is necessary to compile the doc (from master branch)
git checkout master docs satmo
git reset HEAD
cd docs
make html
cd ..
mv -f docs/_build/html/* .
rm -rf satmo docs
git add -A
git commit -m "Generated doc for gh-pages for `git log master -1 --pretty=short --abbrev-commit`"
git push origin gh-pages
