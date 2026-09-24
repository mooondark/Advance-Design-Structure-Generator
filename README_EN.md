# Advance Design Structure Generator

[Français](README.md) | English

Parametric steel structure generator using the Advance Design API.

## Available structures

- **Steel frame**: 3D duo-pitch portal frames, purlins, walls, self-weight
- **Antenna tower**: lattice tower with triangular or square base, configurable number of levels, optional guy wires and anchors

## Features

- Structure selection from a drop-down list
- Sections chosen by family then by name (Advance Design catalogue), with families suited to each member
- Materials: S235, S275, S355, S450, S460
- Interactive 3D preview
- Start and stop the API server from the interface
- Included languages: FR/EN/PL
- Options saved between sessions

## Running

Python 3 must be installed and available in the PATH.

- Double-click `start.bat`: installs or updates the dependencies (streamlit, requests, plotly), then opens the application in the browser
- `start.bat -nodep`: starts without checking the dependencies
- Or: `python -m streamlit run app.py`

## Documentation

- [Version history](CHANGELOG.md) (in French)

**Warning: this script requires the Advance Design [API](https://github.com/Graitec-Group/advance-design-api)**

**A license is also required to use it, and Advance Design 2027 or later must be installed**

See also [Advance Design Viewer](https://github.com/mooondark/ADViewer)
