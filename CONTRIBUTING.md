Contributing
When contributing to this repository, please first discuss the change you wish to make via issue, email, or any other method with the owners of this repository before making a change.

Please note we have a code of conduct, please follow it in all your interactions with the project.


Dependencies
============
* pyvenv
* pytest
* pytest-cov
* pytest-integration


Setup
=====
* Environment
```
python3 -m venv .pyvenv
source ./.pyvenv/bin/activate
pip install pytest pytest-cov pytest-integration wheel
python -m build
```

* Run Tests
```
pytest
```

* Release
```
pip install --upgrade pip
pip install build
python -m build
twine check dist/*
twine upload dist/*
```