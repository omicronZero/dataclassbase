echo Installing dependencies...

# install build script
python -m pip install build twine pkginfo --upgrade --quiet

# remove files from previous build
echo Cleanup previous build...
rm -rf dist dataclassbase.egg-info
rm -rf dist

# build package to dist
echo Building...
python -m build

# test built distribution for errors
echo Testing via twine...
twine check dist/* --strict
