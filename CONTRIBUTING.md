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
pip install -r requirements.txt
pip install pytest pytest-cov wheel
```

* Run Tests
```
pytest
```