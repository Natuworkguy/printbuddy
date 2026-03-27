import os
import sys

def resource_path(relative: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative) # pyright: ignore[reportAttributeAccessIssue]
    return os.path.join(os.path.abspath("."), relative)
