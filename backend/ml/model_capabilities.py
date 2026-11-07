
"""
Detect optional ML capabilities for Astra.

This module is shared by training and serving.
"""

def _gpu_available() -> bool:
    """Check whether a CUDA GPU is available to XGBoost."""
    try:
        import subprocess
        subprocess.check_output(
            ["nvidia-smi"],
            stderr=subprocess.DEVNULL
        )
        return True
    except Exception:
        return False


try:
    import xgboost
    HAS_XGB = True
except Exception:
    HAS_XGB = False


HAS_GPU = HAS_XGB and _gpu_available()
XGB_DEVICE = "cuda" if HAS_GPU else "cpu"
