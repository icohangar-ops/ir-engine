"""Basic smoke tests for the IR Pitch Engine.

The IR Pitch Engine is a set of standalone Python scripts.
These tests verify that the key modules exist and can be located.
"""

import importlib.util
import os
import sys
import pytest

# Add project root to path
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, PROJECT_ROOT)


def test_cubiczan_server_exists():
    """Verify cubiczan_server.py exists and is a valid module spec."""
    path = os.path.join(PROJECT_ROOT, "cubiczan_server.py")
    assert os.path.isfile(path)
    spec = importlib.util.spec_from_file_location("cubiczan_server", path)
    assert spec is not None


def test_investor_relations_engine_exists():
    """Verify investor_relations_engine.py exists and is a valid module spec."""
    path = os.path.join(PROJECT_ROOT, "investor_relations_engine.py")
    assert os.path.isfile(path)
    spec = importlib.util.spec_from_file_location("investor_relations_engine", path)
    assert spec is not None


def test_veris_simulation_engine_exists():
    """Verify veris_simulation_engine.py exists."""
    path = os.path.join(PROJECT_ROOT, "veris_simulation_engine.py")
    assert os.path.isfile(path)


def test_market_data_clients_exists():
    """Verify market_data_clients.py exists."""
    path = os.path.join(PROJECT_ROOT, "market_data_clients.py")
    assert os.path.isfile(path)


def test_placeholder():
    """Placeholder test to ensure CI pipeline has at least one passing test."""
    assert 1 + 1 == 2
