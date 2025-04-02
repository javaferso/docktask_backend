format:
   black src/

lint:
   flake8 src/
   pylint src/

typecheck:
   mypy src/

test:
   pytest
