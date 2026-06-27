import os
import re
import shlex
from pathlib import Path

from profile_manager import DEFAULT_WORKDIR, save_profile


SOURCE = Path(os.environ.get("MULCAT_IMPORT_SOURCE", Path.home() / "AIWorkspace" / "Launcher"))


def read_ps1(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def parse_env(text: str) -> dict[str, str]:
    values = {}
    pattern = re.compile(r"\$env:([A-Za-z_][A-Za-z0-9_]*)\s*=\s*[\"'](.*?)[\"']", re.MULTILINE)
    for key, value in pattern.findall(text):
        values[key] = value
    return values


def parse_workdir(text: str) -> str:
    match = re.search(r"^\s*(?:cd|Set-Location)\s+[\"'](.+?)[\"']", text, re.MULTILINE | re.IGNORECASE)
    return match.group(1) if match else DEFAULT_WORKDIR


def parse_codex_config(text: str) -> dict[str, str | bool | int | float]:
    values = {}
    for item in re.findall(r"-c\s+'([^']+)'", text):
        key, _, raw = item.partition("=")
        if raw in {"true", "false"}:
            values[key] = raw == "true"
        elif raw.startswith('"') and raw.endswith('"'):
            values[key] = raw[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        else:
            try:
                values[key] = int(raw)
            except ValueError:
                values[key] = raw
    return values


def import_claude(path: Path) -> None:
    text = read_ps1(path)
    env = parse_env(text)
    model = env.get("ANTHROPIC_MODEL", "sonnet")
    profile = {
        "id": path.stem,
        "name": path.stem.replace("-", " ").title(),
        "kind": "claude",
        "enabled": True,
        "workingDirectory": parse_workdir(text),
        "terminal": {"mode": "windows-terminal", "keepOpen": True},
        "config": {
            "baseUrl": env.get("ANTHROPIC_BASE_URL", ""),
            "authToken": env.get("ANTHROPIC_AUTH_TOKEN", ""),
            "model": model,
            "sonnetModel": env.get("ANTHROPIC_DEFAULT_SONNET_MODEL", model),
            "opusModel": env.get("ANTHROPIC_DEFAULT_OPUS_MODEL", model),
            "haikuModel": env.get("ANTHROPIC_DEFAULT_HAIKU_MODEL", model),
            "timeoutMs": int(env.get("API_TIMEOUT_MS", "3000000") or 3000000),
            "disableNonessentialTraffic": env.get("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC") == "1",
            "usePowershellTool": env.get("CLAUDE_CODE_USE_POWERSHELL_TOOL") == "1",
            "skipPermissions": "--dangerously-skip-permissions" in text,
            "extraEnv": {},
            "extraArgs": [],
        },
    }
    save_profile(profile)


def import_codex(path: Path) -> None:
    text = read_ps1(path)
    env = parse_env(text)
    c_values = parse_codex_config(text)
    provider_id = str(c_values.get("model_provider", "custom"))
    api_key_env_name = ""
    api_key = ""
    for key, value in env.items():
        api_key_env_name = key
        api_key = value
        break

    prefix = f"model_providers.{provider_id}."
    profile = {
        "id": path.stem,
        "name": path.stem.replace("-", " ").title(),
        "kind": "codex",
        "enabled": True,
        "workingDirectory": parse_workdir(text),
        "terminal": {"mode": "windows-terminal", "keepOpen": True},
        "config": {
            "ignoreUserConfig": "--ignore-user-config" in text,
            "apiKeyEnvName": str(c_values.get(f"{prefix}env_key", api_key_env_name)),
            "apiKey": api_key,
            "provider": {
                "id": provider_id,
                "name": str(c_values.get(f"{prefix}name", provider_id)),
                "baseUrl": str(c_values.get(f"{prefix}base_url", "")),
                "wireApi": str(c_values.get(f"{prefix}wire_api", "responses")),
            },
            "model": str(c_values.get("model", "gpt-5")),
            "reasoningEffort": str(c_values.get("model_reasoning_effort", "high")),
            "disableResponseStorage": bool(c_values.get("disable_response_storage", True)),
            "appsEnabled": bool(c_values.get("features.apps", False)),
            "extraEnv": {},
            "extraConfig": {},
            "extraArgs": [],
        },
    }
    save_profile(profile)


def main() -> None:
    for path in sorted((SOURCE / "ClaudeLauncher").glob("*.ps1")):
        import_claude(path)
    for path in sorted((SOURCE / "CodexLauncher").glob("*.ps1")):
        import_codex(path)
    print("Imported launcher profiles.")


if __name__ == "__main__":
    main()

