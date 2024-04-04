#!/bin/bash

# Change to the directory where the script is located
cd "$(dirname "$0")"

# Remove build, dist and eezo.egg-info directories
echo "Removing old build artifacts..."
rm -rf build dist eezo.egg-info

# Create new distributions
echo "Creating new distribution..."
python setup.py sdist bdist_wheel

# Upload the package to PyPI using twine
echo "Uploading the distribution to PyPI..."
twine upload dist/*

echo "Done."
