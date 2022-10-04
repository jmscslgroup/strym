#!/bin/bash
rm --verbose -rf build/ dist/ *.egg-info*/
python setup_lite.py bdist_wheel --universal
twine upload dist/*
