import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parent
PROFILES_DIR = APP_DIR / "profiles"
SCRIPTS_DIR = APP_DIR / "scripts"
DEFAULT_WORKDIR = str(Path.home() / "AIWorkspace")


class ProfileError(ValueError):
    pass


@dataclass
class LaunchResult:
    ok: bool
    message: str
    script_path: str | None = None


def ensure_dirs() -> None:
    for kind in ("claude", "codex"):
        (PROFILES_DIR / kind).mkdir(parents=True, exist_ok=True)
        (SCRIPTS_DIR / kind).mkdir(parents=True, exist_ok=True)


def profile_path(kind: str, profile_id: str) -> Path:
    safe_kind = validate_kind(kind)
    safe_id = validate_id(profile_id)
    return PROFILES_DIR / safe_kind / f"{safe_id}.json"


def script_path(kind: str, profile_id: str) -> Path:
    safe_kind = validate_kind(kind)
    safe_id = validate_id(profile_id)
    return SCRIPTS_DIR / safe_kind / f"{safe_id}.ps1"


def validate_kind(kind: str) -> str:
    if kind not in {"claude", "codex"}:
        raise ProfileError("Profile kind must be claude or codex.")
    return kind


def validate_id(profile_id: str) -> str:
    cleaned = str(profile_id).strip()
    if not cleaned:
        raise ProfileError("Profile id is required.")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
    if any(ch not in allowed for ch in cleaned):
        raise ProfileError("Profile id may only contain letters, numbers, hyphen, and underscore.")
    return cleaned


def load_profiles() -> list[dict[str, Any]]:
    ensure_dirs()
    profiles: list[dict[str, Any]] = []
    for kind in ("claude", "codex"):
        for path in sorted((PROFILES_DIR / kind).glob("*.json")):
            with path.open("r", encoding="utf-8") as handle:
                profile = json.load(handle)
            profile["_jsonPath"] = str(path)
            profile["_scriptPath"] = str(script_path(profile["kind"], profile["id"]))
            profiles.append(profile)
    return profiles


def save_profile(profile: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_profile(profile)
    path = profile_path(normalized["kind"], normalized["id"])
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    script = generate_script(normalized)
    return {**normalized, "_jsonPath": str(path), "_scriptPath": str(script)}


def delete_profile(kind: str, profile_id: str) -> None:
    profile_path(kind, profile_id).unlink(missing_ok=True)
    script_path(kind, profile_id).unlink(missing_ok=True)


def normalize_profile(profile: dict[str, Any]) -> dict[str, Any]:
    kind = validate_kind(str(profile.get("kind", "")))
    profile_id = validate_id(str(profile.get("id", "")))
    name = str(profile.get("name") or profile_id)
    working_directory = str(profile.get("workingDirectory") or DEFAULT_WORKDIR)
    config = profile.get("config") or {}
    if not isinstance(config, dict):
        raise ProfileError("Profile config must be an object.")

    normalized: dict[str, Any] = {
        "id": profile_id,
        "name": name,
        "kind": kind,
        "enabled": bool(profile.get("enabled", True)),
        "workingDirectory": working_directory,
        "terminal": profile.get("terminal") or {"mode": "windows-terminal", "keepOpen": True},
        "config": config,
    }
    if kind == "claude":
        normalized["config"] = normalize_claude_config(config)
    else:
        normalized["config"] = normalize_codex_config(config)
    return normalized


def normalize_claude_config(config: dict[str, Any]) -> dict[str, Any]:
    model = str(config.get("model") or "sonnet")
    return {
        "baseUrl": str(config.get("baseUrl") or ""),
        "authToken": str(config.get("authToken") or ""),
        "model": model,
        "sonnetModel": str(config.get("sonnetModel") or model),
        "opusModel": str(config.get("opusModel") or model),
        "haikuModel": str(config.get("haikuModel") or model),
        "timeoutMs": int(config.get("timeoutMs") or 3000000),
        "disableNonessentialTraffic": bool(config.get("disableNonessentialTraffic", True)),
        "usePowershellTool": bool(config.get("usePowershellTool", True)),
        "skipPermissions": bool(config.get("skipPermissions", True)),
        "extraEnv": dict(config.get("extraEnv") or {}),
        "extraArgs": list(config.get("extraArgs") or []),
    }


def normalize_codex_config(config: dict[str, Any]) -> dict[str, Any]:
    provider = dict(config.get("provider") or {})
    api_key_env_name = str(config.get("apiKeyEnvName") or "OPENAI_API_KEY")
    return {
        "ignoreUserConfig": bool(config.get("ignoreUserConfig", True)),
        "apiKeyEnvName": api_key_env_name,
        "apiKey": str(config.get("apiKey") or ""),
        "provider": {
            "id": str(provider.get("id") or "custom"),
            "name": str(provider.get("name") or "Custom"),
            "baseUrl": str(provider.get("baseUrl") or ""),
            "wireApi": str(provider.get("wireApi") or "responses"),
        },
        "model": str(config.get("model") or "gpt-5"),
        "reasoningEffort": str(config.get("reasoningEffort") or "high"),
        "disableResponseStorage": bool(config.get("disableResponseStorage", True)),
        "appsEnabled": bool(config.get("appsEnabled", False)),
        "extraEnv": dict(config.get("extraEnv") or {}),
        "extraConfig": dict(config.get("extraConfig") or {}),
        "extraArgs": list(config.get("extraArgs") or []),
    }


def generate_all_scripts() -> list[str]:
    paths = []
    for profile in load_profiles():
        paths.append(str(generate_script(profile)))
    return paths


def generate_script(profile: dict[str, Any]) -> Path:
    normalized = normalize_profile(profile)
    if normalized["kind"] == "claude":
        content = generate_claude_script(normalized)
    else:
        content = generate_codex_script(normalized)
    path = script_path(normalized["kind"], normalized["id"])
    path.write_text(content, encoding="utf-8-sig")
    return path


def generate_claude_script(profile: dict[str, Any]) -> str:
    config = profile["config"]
    env = {
        "ANTHROPIC_BASE_URL": config["baseUrl"],
        "ANTHROPIC_AUTH_TOKEN": config["authToken"],
        "ANTHROPIC_MODEL": config["model"],
        "ANTHROPIC_DEFAULT_SONNET_MODEL": config["sonnetModel"],
        "ANTHROPIC_DEFAULT_OPUS_MODEL": config["opusModel"],
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": config["haikuModel"],
        "API_TIMEOUT_MS": str(config["timeoutMs"]),
        **{str(k): str(v) for k, v in config.get("extraEnv", {}).items()},
    }
    if config["disableNonessentialTraffic"]:
        env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
    if config["usePowershellTool"]:
        env["CLAUDE_CODE_USE_POWERSHELL_TOOL"] = "1"

    args = ["--dangerously-skip-permissions"] if config["skipPermissions"] else []
    args.extend(str(arg) for arg in config.get("extraArgs", []))
    lines = script_header(profile)
    lines.extend(env_lines(env))
    command = "claude" + ps_args(args)
    lines.append(command)
    return "\n".join(lines) + "\n"


def generate_codex_script(profile: dict[str, Any]) -> str:
    config = profile["config"]
    provider = config["provider"]
    env = {config["apiKeyEnvName"]: config["apiKey"]}
    env.update({str(k): str(v) for k, v in config.get("extraEnv", {}).items()})

    provider_id = provider["id"]
    c_values: dict[str, Any] = {
        "model_provider": provider_id,
        "model": config["model"],
        "model_reasoning_effort": config["reasoningEffort"],
        "disable_response_storage": config["disableResponseStorage"],
        "features.apps": config["appsEnabled"],
        f"model_providers.{provider_id}.name": provider["name"],
        f"model_providers.{provider_id}.base_url": provider["baseUrl"],
        f"model_providers.{provider_id}.env_key": config["apiKeyEnvName"],
        f"model_providers.{provider_id}.wire_api": provider["wireApi"],
    }
    c_values.update(config.get("extraConfig", {}))

    lines = script_header(profile)
    lines.extend(env_lines(env))
    parts = ["codex"]
    if config["ignoreUserConfig"]:
        parts.append("--ignore-user-config")
    parts.extend(str(arg) for arg in config.get("extraArgs", []))
    for key, value in c_values.items():
        parts.append("-c")
        parts.append(toml_assignment(key, value))
    lines.append(ps_multiline_command(parts))
    return "\n".join(lines) + "\n"


def script_header(profile: dict[str, Any]) -> list[str]:
    return [
        f"# Generated by MulCat from profiles/{profile['kind']}/{profile['id']}.json",
        "$ErrorActionPreference = 'Stop'",
        f"Set-Location {ps_quote(profile['workingDirectory'])}",
        "",
    ]


def env_lines(env: dict[str, str]) -> list[str]:
    lines = []
    for key, value in env.items():
        if value != "":
            lines.append(f"$env:{key} = {ps_quote(value)}")
    lines.append("")
    return lines


def ps_quote(value: Any) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def ps_args(args: list[str]) -> str:
    if not args:
        return ""
    return " " + " ".join(ps_quote(arg) for arg in args)


def ps_multiline_command(parts: list[str]) -> str:
    rendered = []
    for index, part in enumerate(parts):
        token = part if index == 0 else ps_quote(part)
        suffix = " `" if index < len(parts) - 1 else ""
        rendered.append(f"  {token}{suffix}" if index else f"{token}{suffix}")
    return "\n".join(rendered)


def toml_assignment(key: str, value: Any) -> str:
    if isinstance(value, bool):
        rendered = "true" if value else "false"
    elif isinstance(value, (int, float)):
        rendered = str(value)
    else:
        escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
        rendered = f'"{escaped}"'
    return f"{key}={rendered}"


def launch_profile(kind: str, profile_id: str) -> LaunchResult:
    path = script_path(kind, profile_id)
    if not path.exists():
        profile = json.loads(profile_path(kind, profile_id).read_text(encoding="utf-8"))
        path = generate_script(profile)

    try:
        wt = shutil.which("wt.exe") or shutil.which("wt")
        if wt:
            subprocess.Popen(
                [
                    wt,
                    "new-tab",
                    "powershell.exe",
                    "-NoExit",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(path),
                ],
                cwd=str(APP_DIR),
                close_fds=True,
            )
        else:
            subprocess.Popen(
                [
                    "powershell.exe",
                    "-NoExit",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(path),
                ],
                cwd=str(APP_DIR),
                close_fds=True,
            )
        return LaunchResult(True, f"Launched {profile_id}.", str(path))
    except Exception as exc:
        return LaunchResult(False, f"Launch failed: {exc}", str(path))

