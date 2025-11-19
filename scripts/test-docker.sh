#!/bin/bash
# Script to run tests in Docker (Ubuntu/CI environment)

set -e

echo "Building Docker test image..."
docker-compose -f docker-compose.test.yml build

echo "Running tests in Docker..."
docker-compose -f docker-compose.test.yml run --rm test "$@"

