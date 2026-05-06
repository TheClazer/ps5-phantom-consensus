"""
Tests for @trace_and_validate decorator.
"""
from __future__ import annotations
import math
import pytest
from src.sanitization import trace_and_validate
from src.sanitization.decorators import GhostSponsorError


def test_id_normalization():
    """Test that IDs are normalized to canonical format."""
    
    @trace_and_validate
    def process_data(data: dict) -> dict:
        return data
    
    input_data = {
        'representatives': [
            {'id': 'REP_001', 'name': 'Alice'},
            {'id': 'rep-2', 'name': 'Bob'},
            {'id': ' Rep 3 ', 'name': 'Charlie'},
        ],
        'proposals': [
            {'id': 'PROP_001', 'sponsor': 'REP_001'},
            {'id': 'prop-2', 'sponsor': 'rep-2'},
        ]
    }
    
    result = process_data(input_data)
    
    # Check normalization
    assert result['representatives'][0]['id'] == 'rep_001'
    assert result['representatives'][1]['id'] == 'rep_002'
    assert result['representatives'][2]['id'] == 'rep_003'
    assert result['proposals'][0]['id'] == 'prop_001'
    assert result['proposals'][0]['sponsor'] == 'rep_001'
    assert result['proposals'][1]['id'] == 'prop_002'
    assert result['proposals'][1]['sponsor'] == 'rep_002'


def test_nan_detection():
    """Test that NaN values are detected and logged."""
    
    @trace_and_validate
    def process_numbers(data: list) -> list:
        return data
    
    input_data = [
        {'value': 1.0},
        {'value': math.nan},
        {'value': 3.0},
    ]
    
    # Should not crash, just log warning
    result = process_numbers(input_data)
    assert len(result) == 3


def test_ghost_sponsor_quarantine():
    """Test that Ghost Sponsor errors are caught and quarantined."""
    
    @trace_and_validate
    def load_proposals(proposals: list) -> list:
        # Simulate ghost sponsor detection
        for p in proposals:
            if p.get('sponsor') == 'rep_999':
                raise GhostSponsorError(f"Proposal {p['id']} references unknown sponsor rep_999")
        return proposals
    
    input_data = [
        {'id': 'prop_001', 'sponsor': 'rep_001'},
        {'id': 'prop_002', 'sponsor': 'rep_999'},  # Ghost sponsor
    ]
    
    # Should not crash — decorator catches GhostSponsorError
    result = load_proposals(input_data)
    
    # Returns safe default (empty list for 'load' functions)
    assert result == []


def test_input_size_logging():
    """Test that input size is logged."""
    
    @trace_and_validate
    def process_large_data(data: dict) -> int:
        return len(data.get('items', []))
    
    input_data = {
        'items': [{'id': i} for i in range(100)],
        'metadata': {'count': 100}
    }
    
    result = process_large_data(input_data)
    assert result == 100


def test_nested_id_normalization():
    """Test that nested IDs are normalized."""
    
    @trace_and_validate
    def process_relationships(data: dict) -> dict:
        return data
    
    input_data = {
        'relationships': [
            {'from_rep': 'REP_001', 'to_rep': 'rep-2'},
            {'from_rep': ' Rep 3 ', 'to_rep': 'REP_004'},
        ]
    }
    
    result = process_relationships(input_data)
    
    assert result['relationships'][0]['from_rep'] == 'rep_001'
    assert result['relationships'][0]['to_rep'] == 'rep_002'
    assert result['relationships'][1]['from_rep'] == 'rep_003'
    assert result['relationships'][1]['to_rep'] == 'rep_004'


def test_decorator_preserves_function_metadata():
    """Test that decorator preserves original function metadata."""
    
    @trace_and_validate
    def my_function(x: int) -> int:
        """This is my function."""
        return x * 2
    
    assert my_function.__name__ == 'my_function'
    assert my_function.__doc__ == 'This is my function.'


def test_exception_passthrough():
    """Test that non-GhostSponsor exceptions are re-raised."""
    
    @trace_and_validate
    def failing_function(data: dict) -> dict:
        raise ValueError("Something went wrong")
    
    with pytest.raises(ValueError, match="Something went wrong"):
        failing_function({'test': 'data'})
