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

`profiles/` and `scripts/` are part of the runtime structure. Git tracks only `.gitkeep` files in those folders; every real profile JSON and generated PS1 script stays local.

Examples live under `examples/`.

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

Copy examples from `examples/` into `profiles/` or `scripts/` for local use. Files created there are ignored by git.

## Maintenance

The private working project `MultiCaat` and public release project `MulCat` should receive the same application logic changes. Runtime data is not shared: profile JSON files and PS1 scripts created in `MultiCaat` must never be copied or committed to `MulCat`.
