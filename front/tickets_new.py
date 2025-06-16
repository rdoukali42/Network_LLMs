# filepath: /Users/level3/Desktop/Network/front/tickets.py
"""
Ticket system entry point for Streamlit app.
This file has been refactored into a modular structure.
The main functionality is now in the tickets/ subdirectory.
"""

from tickets import show_ticket_interface


def main():
    """Main entry point for the ticket system."""
    show_ticket_interface()


# For backwards compatibility, expose the main function as the old interface name
show_ticket_interface = show_ticket_interface
