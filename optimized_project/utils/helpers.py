"""
Utility functions for the optimized_project.
"""

from pathlib import Path
import logging # Keep logging if used by helpers

logger = logging.getLogger(__name__)

def ensure_directory_exists(dir_path: Path) -> None:
    """
    Ensures a directory exists, creating it if it doesn't.
    Args:
        dir_path: A Path object representing the directory.
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        # print(f"Directory ensured: {dir_path}")
    except Exception as e:
        logger.error(f"Error creating directory {dir_path}: {e}")
        # Depending on severity, could re-raise or handle

# Other general-purpose helper functions can be added here as needed.
# For example, date formatting, string manipulation, etc. if they are
# used by multiple modules across different layers (app, core, data_management).

# Example:
# def format_timestamp_for_display(iso_timestamp_str: str) -> str:
#     from datetime import datetime
#     try:
#         dt_obj = datetime.fromisoformat(iso_timestamp_str)
#         return dt_obj.strftime("%Y-%m-%d %H:%M:%S")
#     except (ValueError, TypeError):
#         return iso_timestamp_str # Return original if parsing fails

if __name__ == '__main__':
    # Example usage
    test_dir = Path("./temp_test_dir/subdir")
    print(f"Ensuring directory: {test_dir.resolve()}")
    ensure_directory_exists(test_dir)
    if test_dir.exists() and test_dir.is_dir():
        print(f"Directory {test_dir.resolve()} exists.")
        # Clean up
        # import shutil
        # shutil.rmtree("./temp_test_dir")
        # print("Cleaned up temp_test_dir.")
    else:
        print(f"Failed to create or verify {test_dir.resolve()}")
