# burglekutt Makefile

.PHONY: test clean

# Default target
test:
	@python3 -m unittest discover -s tests

# Clean (no build artifacts for this project)
clean:
	@echo "Nothing to clean."
