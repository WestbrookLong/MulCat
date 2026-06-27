# Maintenance Rule

Keep `MultiCaat` and `MulCat` application logic in sync.

- Apply UI, generator, launcher, and desktop API logic changes to both projects.
- Keep local runtime data separate.
- Never copy or commit real `profiles/**/*.json` files from `MultiCaat` to `MulCat`.
- Never copy or commit real `scripts/**/*.ps1` files from `MultiCaat` to `MulCat`.
- Use `examples/` for public placeholder profiles and scripts.

