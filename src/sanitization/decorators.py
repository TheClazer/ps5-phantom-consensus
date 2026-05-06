"""
Decorators for data sanitization and validation.

@trace_and_validate:
  - Logs input size
  - Checks for NaN values
  - Normalizes IDs to lowercase canonical format
  - Catches Ghost Sponsor errors and logs 'Strategic Quarantine' events
"""
from __future__ import annotations
import functools
import logging
import re
from typing import Any, Callable, TypeVar
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('phantom_consensus.sanitization')

# Type variable for generic function decoration
F = TypeVar('F', bound=Callable[..., Any])

# ID normalization patterns
_REP_PATTERN = re.compile(r'^(?:rep|REP|Rep)[_\-\s]?(\d+)$', re.IGNORECASE)
_PROP_PATTERN = re.compile(r'^(?:prop|PROP|Prop)[_\-\s]?(\d+)$', re.IGNORECASE)


class GhostSponsorError(Exception):
    """Raised when a proposal references a non-existent sponsor."""
    pass


def _normalize_id(raw_id: Any) -> str | None:
    """
    Normalize IDs to lowercase canonical format.
    
    Examples:
      'REP_001' → 'rep_001'
      'rep-1'   → 'rep_001'
      ' Rep 2 ' → 'rep_002'
      'PROP_5'  → 'prop_005'
    """
    if not isinstance(raw_id, str):
        return None
    
    cleaned = raw_id.strip()
    
    # Try representative pattern
    match = _REP_PATTERN.match(cleaned)
    if match:
        return f"rep_{match.group(1).zfill(3)}"
    
    # Try proposal pattern
    match = _PROP_PATTERN.match(cleaned)
    if match:
        return f"prop_{match.group(1).zfill(3)}"
    
    # Fallback: lowercase and normalize delimiters
    return cleaned.lower().replace('-', '_').replace(' ', '_')


def _check_nan_values(data: Any, path: str = "root") -> list[str]:
    """
    Recursively check for NaN values in data structures.
    Returns list of paths where NaN was found.
    """
    nan_paths: list[str] = []
    
    if isinstance(data, float) and math.isnan(data):
        nan_paths.append(path)
    elif isinstance(data, dict):
        for key, value in data.items():
            nan_paths.extend(_check_nan_values(value, f"{path}.{key}"))
    elif isinstance(data, (list, tuple)):
        for i, item in enumerate(data):
            nan_paths.extend(_check_nan_values(item, f"{path}[{i}]"))
    
    return nan_paths


def _normalize_data_ids(data: Any) -> Any:
    """
    Recursively normalize all ID fields in data structures.
    Handles dicts, lists, and dataclass-like objects.
    """
    if isinstance(data, dict):
        normalized = {}
        for key, value in data.items():
            # Normalize ID fields
            if key in ('id', 'rep_id', 'from_rep', 'to_rep', 'sponsor', 'sponsor_id', 'proposal_id'):
                normalized[key] = _normalize_id(value) if value is not None else None
            else:
                normalized[key] = _normalize_data_ids(value)
        return normalized
    elif isinstance(data, list):
        return [_normalize_data_ids(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(_normalize_data_ids(item) for item in data)
    elif hasattr(data, '__dict__'):
        # Handle dataclass-like objects
        for attr in ('id', 'rep_id', 'from_rep', 'to_rep', 'sponsor_id', 'proposal_id'):
            if hasattr(data, attr):
                raw_value = getattr(data, attr)
                if raw_value is not None:
                    setattr(data, attr, _normalize_id(raw_value))
        return data
    else:
        return data


def _get_data_size(data: Any) -> dict[str, int]:
    """
    Calculate size metrics for input data.
    Returns dict with counts of various data types.
    """
    size_info = {
        'total_items': 0,
        'dicts': 0,
        'lists': 0,
        'primitives': 0,
    }
    
    if isinstance(data, dict):
        size_info['dicts'] += 1
        size_info['total_items'] += len(data)
        for value in data.values():
            sub_size = _get_data_size(value)
            for key in size_info:
                size_info[key] += sub_size[key]
    elif isinstance(data, (list, tuple)):
        size_info['lists'] += 1
        size_info['total_items'] += len(data)
        for item in data:
            sub_size = _get_data_size(item)
            for key in size_info:
                size_info[key] += sub_size[key]
    else:
        size_info['primitives'] += 1
    
    return size_info


def trace_and_validate(func: F) -> F:
    """
    Decorator that:
      1. Logs input size
      2. Checks for NaN values
      3. Normalizes all IDs to lowercase canonical format
      4. Catches Ghost Sponsor errors and logs 'Strategic Quarantine' events
    
    Usage:
        @trace_and_validate
        def my_function(data):
            # ... process data ...
            return result
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        
        # ── Step 1: Log input size ────────────────────────────────────────────
        try:
            # Combine args and kwargs for size calculation
            all_inputs = list(args) + list(kwargs.values())
            total_size = {'total_items': 0, 'dicts': 0, 'lists': 0, 'primitives': 0}
            for inp in all_inputs:
                size_info = _get_data_size(inp)
                for key in total_size:
                    total_size[key] += size_info[key]
            
            logger.info(
                f"[{func_name}] Input size: {total_size['total_items']} items "
                f"({total_size['dicts']} dicts, {total_size['lists']} lists, "
                f"{total_size['primitives']} primitives)"
            )
        except Exception as e:
            logger.warning(f"[{func_name}] Could not calculate input size: {e}")
        
        # ── Step 2: Check for NaN values ──────────────────────────────────────
        try:
            nan_paths: list[str] = []
            for i, arg in enumerate(args):
                nan_paths.extend(_check_nan_values(arg, f"arg[{i}]"))
            for key, value in kwargs.items():
                nan_paths.extend(_check_nan_values(value, f"kwarg.{key}"))
            
            if nan_paths:
                logger.warning(
                    f"[{func_name}] NaN values detected at: {', '.join(nan_paths[:5])}"
                    + (f" (and {len(nan_paths) - 5} more)" if len(nan_paths) > 5 else "")
                )
        except Exception as e:
            logger.warning(f"[{func_name}] Could not check for NaN values: {e}")
        
        # ── Step 3: Normalize IDs ─────────────────────────────────────────────
        try:
            normalized_args = [_normalize_data_ids(arg) for arg in args]
            normalized_kwargs = {k: _normalize_data_ids(v) for k, v in kwargs.items()}
            
            logger.debug(f"[{func_name}] ID normalization complete")
        except Exception as e:
            logger.warning(f"[{func_name}] ID normalization failed: {e}")
            normalized_args = args
            normalized_kwargs = kwargs
        
        # ── Step 4: Execute function with Ghost Sponsor handling ──────────────
        try:
            result = func(*normalized_args, **normalized_kwargs)
            logger.info(f"[{func_name}] Execution successful")
            return result
        
        except GhostSponsorError as e:
            # Strategic Quarantine: log and return safe default instead of crashing
            logger.warning(
                f"[{func_name}] Strategic Quarantine: Ghost Sponsor detected - {e}"
            )
            logger.info(
                f"[{func_name}] Quarantined entity excluded from consensus. "
                "Continuing with valid data."
            )
            # Return safe default based on function name heuristics
            if 'load' in func_name or 'parse' in func_name:
                return []  # Empty list for loaders
            elif 'build' in func_name or 'compute' in func_name:
                return {}  # Empty dict for builders
            else:
                return None  # None for other functions
        
        except Exception as e:
            logger.error(f"[{func_name}] Execution failed: {type(e).__name__}: {e}")
            raise
    
    return wrapper  # type: ignore
