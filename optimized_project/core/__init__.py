# Makes 'core' a package, grouping main backend logic.

from .system import AISystem

# Expose sub-packages if direct import like 'from core.agents import ...' is desired by users of 'core'
# from . import agents
# from . import tools
# from . import graph
# from . import services
# from . import models

__all__ = [
    "AISystem"
    # "agents", # if exposing sub-packages
    # "tools",
    # "graph",
    # "services",
    # "models"
]
