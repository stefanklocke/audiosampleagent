# audiosampleagent
Audio Sample Agent

## Development Setup
### Create virtual environment
- Run `python -m venv .venv` to create a folder `.venv` containing the virtual environment
- Activate the virtual environment by using `source .venv/bin/activate`
- Note that the folder `.venv*/` should be listed in the `.gitignore` file

### Requirements
Install PortAudio:
- sudo apt-get install libasound-dev
- sudo apt-get install libportaudio2

### Misc Configurations
#### Jupyter "Run Current Cell" Fix
Add to keybindings.json (bring it up via CTRL+Shift+P and type "Open Keyboard Shortcuts (JSON)"):
```
{
        "key": "ctrl+enter",
        "command": "notebook.cell.execute",
        "when": "notebookCellListFocused"
}
```