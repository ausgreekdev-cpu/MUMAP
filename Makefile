.PHONY: package install uninstall clean migrate revision db-stamp

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
	@python3 -m uvicorn backend.main:app --reload --port 8000

# Run tests
test:
	@python3 tests/test_agents.py
	@python3 -m pytest backend/tests -q

# Backend API tests only
test-backend:
	@python3 -m pytest backend/tests -q

# Apply pending migrations
migrate:
	@python3 -m alembic upgrade head

# Generate a new revision from model changes: make revision msg="add thing"
revision:
	@python3 -m alembic revision --autogenerate -m "$(msg)"

# Mark an existing create_all-era DB as fully migrated (does not alter data)
db-stamp:
	@python3 -m alembic stamp head

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
	@echo "  make test     - Run all tests (legacy + pytest)"
	@echo "  make clean    - Clean build artifacts"
	@echo "  make dev      - Run development server"
	@echo "  make migrate  - Apply pending DB migrations (alembic upgrade head)"
	@echo "  make revision - Autogenerate a migration from model changes (msg=...)"
	@echo "  make db-stamp - Stamp an existing create_all DB as migrated"
	@echo "  make example1 - Run simple example"
	@echo "  make example2 - Run research team example"
