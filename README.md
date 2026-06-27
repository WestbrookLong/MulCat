# MulCat

MulCat is a Windows desktop launcher for Claude and Codex profiles.

It stores launcher profiles as JSON and generates runnable PowerShell scripts from those profiles. The generated scripts set process-level environment variables and then launch the selected CLI.

## Project Structure

```text
desktop_client.py              pywebview desktop shell
profile_manager.py             profile loading, saving, PS1 generation, launch logic
import_existing_launcher.py     optional importer for existing launcher scripts
desktop_ui/                    Vite + React frontend
profiles/                      local JSON profiles
scripts/                       generated or hand-edited PowerShell launch scripts
```

`profiles/` and `scripts/` are part of the runtime structure. Only placeholder example files are tracked by git. Your real local profiles and scripts should stay untracked.

## Development

```powershell
cd desktop_ui
npm install
npm run build
cd ..
python desktop_client.py
```

You can also run:

```powershell
.\start_desktop_client.bat
```

## Security

Do not commit real API keys, auth tokens, private base URLs, generated scripts, logs, or local build output.

If you copy an example profile, rename it to something other than `example*.json`; `.gitignore` will keep it local.

