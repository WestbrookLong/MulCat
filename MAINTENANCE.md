# Maintenance Rule

Keep `MultiCaat` and `MulCat` application logic in sync.

- Apply UI, generator, launcher, and desktop API logic changes to both projects.
- Keep shared application behavior in `mulcat_core/`.
- Keep `windows/` and `mac/` limited to launch methods and platform-only adapter code.
- Treat the PowerShell profile/script generator in `mulcat_core/profile_manager.py` as the single source of truth for both Windows and macOS.
- Keep local runtime data separate.
- Never copy or commit real `profiles/**/*.json` files from `MultiCaat` to `MulCat`.
- Never copy or commit real `scripts/**/*.ps1` files from `MultiCaat` to `MulCat`.
- Use `examples/` for public placeholder profiles and scripts.
