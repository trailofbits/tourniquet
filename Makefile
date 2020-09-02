ALL_CXX_SRCS := $(shell find transformer -name '*.cpp' -o -name '*.h')

ALL_PY_SRCS := setup.py \
	$(shell find tourniquet -name '*.py') \
	$(shell find tests -name '*.py')

.PHONY: all
all:
	@echo "Run my targets individually!"

env:
	test -d env || python3 -m venv env && \
		. env/bin/activate && \
		pip install --upgrade pip

.PHONY: dev
dev: env
	. env/bin/activate && \
		pip install -r dev-requirements.txt


.PHONY: build
build: env
	. env/build/activate && \
		pip install .

.PHONY: py-lint
py-lint:
	. env/bin/activate && \
		black $(ALL_PY_SRCS) && \
		isort $(ALL_PY_SRCS) && \
		flake8 $(ALL_PY_SRCS)


.PHONY: cxx-lint
cxx-lint:
	clang-format -i $(ALL_CXX_SRCS)

.PHONY: lint
lint: py-lint cxx-lint
	git diff --exit-code

.PHONY: typecheck
typecheck:
	. env/bin/activate && \
		mypy tourniquet

.PHONY: test
test: build
	. env/bin/activate && \
		pytest tests/

.PHONY: test-cov
test-cov:
	. env/bin/activate && \
		pytest --cov=tourniquet/ tests/

.PHONY: doc
doc:
	. env/bin/activate && \
		PYTHONWARNINGS='error::UserWarning' pdoc --force --html tourniquet

.PHONY: edit
edit:
	$(EDITOR) $(ALL_PY_SRCS)
