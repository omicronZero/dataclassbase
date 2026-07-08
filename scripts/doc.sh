# delete previous versions
rm -rf docs/build
rm -rf docs/source/_autogen

# build ReST from source
sphinx-apidoc -o docs/source/_autogen .

# build documentation from ReST
sphinx-build -M html docs/source docs/build
