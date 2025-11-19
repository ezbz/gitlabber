#!/bin/bash
# Script to run tests in Docker (Ubuntu environment)

set -e

echo "🐳 Building Docker test image..."
docker-compose -f docker-compose.test.yml build

echo ""
echo "🧪 Running tests in Docker (Ubuntu)..."
echo ""

# Run specific tests that are skipped
docker-compose -f docker-compose.test.yml run --rm test \
    python -m pytest tests/test_cli.py tests/test_integration.py -v --tb=short -k "test_version_option or test_missing_token_error or test_missing_url_error or test_missing_dest_error or test_print_tree or test_sync_tree or test_help or test_version"

echo ""
echo "✅ Docker tests complete!"

