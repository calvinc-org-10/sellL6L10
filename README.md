# L6-L10 Sales Helper

A desktop application for tracking L6 to L10 sales and picking operations.

## Overview

The L6-L10 Sales Helper is a PySide6-based GUI application designed to streamline sales tracking and inventory picking workflows. It provides an intuitive interface for managing work orders, parts, and related data through customizable forms and database-backed storage.

## Features

- **Menu-driven Interface**: Easy-to-navigate menu system for accessing different functions
- **Database Management**: SQLAlchemy-based ORM for robust data persistence
- **Form Management**: Flexible form system with dirty tracking and validation
- **Work Order Tracking**: Manage work orders with support for embedded subforms
- **Parts Management**: Track parts inventory and requirements
- **Excel Integration**: Import/export capabilities for data interoperability

## Prerequisites

- Python 3.8 or higher
- Qt 6 (installed via PySide6)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/calvinc-org-10/sellL6L10.git
   cd sellL6L10
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
python Main.py
```

The application will launch with a main window showing the menu system. Navigate through the menu to access various features.

## Project Structure

```
sellL6L10/
├── Main.py                      # Application entry point
├── MainScreen.py                # Main window UI
├── requirements.txt             # Python dependencies
├── sysver.py                    # Version information
├── app/                         # Core application modules
│   ├── database.py              # Database configuration
│   ├── models.py                # Data models
│   └── forms.py                 # Form definitions
├── cMenu/                       # Menu system and utilities
│   ├── cMenu.py                 # Main menu component
│   ├── database.py              # Menu database integration
│   ├── models.py                # Menu-related models
│   └── utils/                   # Utility modules
├── assets/                      # Static resources
└── *.sqlite                     # Database files
```

## Technologies

- **PySide6**: Qt 6 bindings for Python (GUI framework)
- **SQLAlchemy**: SQL toolkit and ORM
- **openpyxl**: Excel file handling
- **QtAwesome**: Icon fonts for Qt applications

## Development

### Version Information

Current version: 1.0.0 (DEV)

See `sysver.py` for version details and release history.

### Database

The application uses SQLite databases for data storage:
- `sellL6L10.sqlite`: Main application database
- `cMenudb.sqlite`: Menu configuration database

## License

See [LICENSE](LICENSE) file for details.

## Contributing

This is a specialized internal tool for L6-L10 sales operations. For questions or support, please contact the development team.

## Notes

- See `_notes.md` for detailed technical documentation about the form system architecture
- Check `todo.txt` for ongoing development tasks
