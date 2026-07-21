# scripts/

Convenience scripts. **None of these are required** — every command they
run is also documented plainly in the root `README.md`. Use whichever you
prefer.

| Script | Platform | Purpose |
|---|---|---|
| `setup-backend.ps1` / `.sh` | Windows / macOS·Linux | Create `apps/api/.venv` and install Python dependencies |
| `dev-backend.ps1` / `.sh` | Windows / macOS·Linux | Run the FastAPI dev server on port 8000 |
| `dev-desktop.ps1` / `.sh` | Windows / macOS·Linux | Run the Tauri desktop app in dev mode |

On Windows, if script execution is blocked, run PowerShell as
Administrator once and execute:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
