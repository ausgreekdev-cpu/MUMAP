.PHONY: package install uninstall clean

VERSION = 1.0.0
PACKAGE_NAME = multi-agent-platform

# Create package
package:
	@echo "Creating package..."
	@tar czf $(PACKAGE_NAME)-$(VERSION)-linux-x64.tar.gz \
		--exclude='*.pyc' \
		--exclude='__pycache__' \
		--exclude='*.db' \
		--exclude='node_modules' \
		--exclude='.git' \
		src/ \
		backend/ \
		examples/ \
		tests/ \
		installer/ \
		README.md \
		requirements.txt
	@echo "Package created: $(PACKAGE_NAME)-$(VERSION)-linux-x64.tar.gz"

# Install
install:
	@sudo ./installer/scripts/install.sh

# Uninstall
uninstall:
	@sudo ./installer/scripts/uninstall.sh

# Clean
clean:
	@rm -f $(PACKAGE_NAME)-*.tar.gz
	@rm -f *.db
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned"

# Development mode (run locally)
dev:
	@cd backend && python3 -m uvicorn main:app --reload --port 8000

# Run tests
test:
	@python3 tests/test_agents.py

# Run examples
example1:
	@python3 examples/simple_agents.py

example2:
	@python3 examples/research_team.py

help:
	@echo "Available commands:"
	@echo "  make package  - Create installable package"
	@echo "  make install  - Install to system"
	@echo "  make uninstall - Remove from system"
	@echo "  make clean    - Clean build artifacts"
	@echo "  make dev      - Run development server"
	@echo "  make test     - Run tests"
	@echo "  make example1 - Run simple example"
	@echo "  make example2 - Run research team example"
