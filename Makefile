PYTHON = python3

.PHONY: reinstall install upload uninstall rebuild build clean test

reinstall:
	make uninstall
	make rebuild
	make install
	make clean

install: dist/*.whl
	$(PYTHON) -m pip install dist/*.whl
	$(PYTHON) -m pip show multi-tldr

upload: dist/*.whl dist/*.tar.gz
	$(PYTHON) -m twine check dist/*.whl dist/*.tar.gz
	# username is: __token__
	$(PYTHON) -m twine upload dist/*.whl dist/*.tar.gz

uninstall:
	$(PYTHON) -m pip uninstall -y multi-tldr

rebuild build dist/*.whl dist/*.tar.gz: ./setup.py ./tldr.py
	# make sure clean old versions
	make clean

	make test

	$(PYTHON) ./setup.py sdist bdist_wheel

	# 'pip install' is buggy when .egg-info exist
	rm -rf *.egg-info build

clean:
	rm -rf *.egg-info build dist

test:
	$(PYTHON) ./test.py -vv

