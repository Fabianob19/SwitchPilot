import sys
# Force zstandard to allow urllib3 to fail gracefully
sys.modules['zstandard'] = None
