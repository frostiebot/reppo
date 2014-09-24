.PHONY: clean-pyc coverage

test:
	@nosetests -s --verbosity=2

coverage:
	@nosetests -c ./nose.cfg

# Cleaning

clean: clean-pyc

clean-pyc:
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +
