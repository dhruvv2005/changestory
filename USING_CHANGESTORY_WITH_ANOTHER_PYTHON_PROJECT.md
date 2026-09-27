# Use ChangeStory With Another Python Project

This guide explains how to run ChangeStory against a Python project on Windows.
ChangeStory analyzes Git changes and reports changed symbols, direct callers,
potential risks, and suggested tests. It does not execute the target project's
tests.

## Requirements

- Windows and PowerShell
- Python 3.11 or newer
- Git
- Node.js and npm (needed for the interactive browser dashboard)

## One-Time ChangeStory Setup

Clone ChangeStory and install its CLI in a virtual environment:

```powershell
git clone https://github.com/dhruvv2005/changestory.git
cd changestory
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .\cli
```

Install the dashboard dependencies once if you want the interactive report in a
browser:

```powershell
Push-Location frontend
npm install
Pop-Location
```

Keep the ChangeStory virtual environment active when using the `changestory`
command. For the CLI workflow below, you do not need to start either server
manually: the CLI starts the local backend when needed. If the dashboard
dependencies are installed, it also starts the dashboard and opens the report.
If a server is already running on the default port, the CLI reuses it.

## Analyze Another Python Project

First, make sure the ChangeStory virtual environment is active. Then go to the
target project folder. The target must be a Git repository. If it is not already
one, initialize Git and make an initial commit before analyzing changes:

```powershell
cd "D:\path\to\your-python-project"
git init
git add .
git commit -m "Initial commit"
```

For an existing Git repository, do not repeat `git init` or the initial commit.
Go to its root and initialize ChangeStory once:

```powershell
cd "D:\path\to\your-python-project"
changestory init
```

Now make and save the code changes you want to analyze, then run:

```powershell
changestory analyze
```

The CLI collects staged and unstaged Git changes, plus untracked Python files,
and analyzes them with the local repository as context. The report includes a
browser URL and local export URLs. Git-ignored files are not analyzed.

You can also run the commands from another working directory by supplying the
project path:

```powershell
changestory init --repo "D:\path\to\your-python-project"
changestory analyze --repo "D:\path\to\your-python-project"
```

## Troubleshooting

- **`changestory` is not recognized:** activate the ChangeStory virtual
  environment, or run its executable directly:

  ```powershell
  & "C:\path\to\changestory\venv\Scripts\changestory.exe" analyze --repo "D:\path\to\your-python-project"
  ```

- **No diff changes detected:** save your edits and check `git status` in the
  target project. Confirm that files are not ignored by Git and that there are
  staged or unstaged changes, or new `.py` files.

- **Browser dashboard does not open:** run `npm install` in ChangeStory's
  `frontend` folder, then try `changestory analyze` again. The backend report
  remains available at the local report URL printed by the CLI.

- **Windows Unicode decode error:** after the encoding fix is pushed to GitHub,
  update ChangeStory and reinstall the editable CLI from the active environment:

  ```powershell
  cd "C:\path\to\changestory"
  git pull
  python -m pip install -e .\cli
  ```

ChangeStory currently analyzes Python code using static analysis. Dynamic
imports, reflection, and runtime dispatch may not be detected, and the target
project's tests must be run separately using that project's own test command.