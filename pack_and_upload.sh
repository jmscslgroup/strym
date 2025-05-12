#!/bin/bash
rm -rf build/ dist/ *.egg-info*/
uv build
#python setup.py bdist_wheel --universal
mv dist/strym-1.0.0-cp39-abi3-linux_x86_64.whl dist/strym-1.0.0-cp39-abi3-manylinux_2_28_x86_64.whl
twine upload dist/*
