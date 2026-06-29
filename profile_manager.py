import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = app_dir()
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
                profile = normalize_profile(json.load(handle))
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


def save_script_and_sync_profile(kind: str, profile_id: str, text: str) -> dict[str, Any]:
    safe_kind = validate_kind(kind)
    safe_id = validate_id(profile_id)
    script = script_path(safe_kind, safe_id)
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(str(text), encoding="utf-8-sig")

    path = profile_path(safe_kind, safe_id)
    if not path.exists():
        raise ProfileError(f"Profile does not exist: {safe_id}.")
    profile = normalize_profile(json.loads(path.read_text(encoding="utf-8")))
    if safe_kind == "claude":
        profile = sync_claude_script_to_profile(profile, str(text))
    else:
        profile = sync_codex_script_to_profile(profile, str(text))
    normalized = normalize_profile(profile)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
        "provider": str(profile.get("provider") or ""),
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
    models = dict(config.get("models") or {})
    launch = dict(config.get("launch") or {})
    advanced = dict(config.get("advanced") or {})

    old_model = str(config.get("model") or "")
    old_sonnet = str(config.get("sonnetModel") or "")
    old_opus = str(config.get("opusModel") or "")
    old_haiku = str(config.get("haikuModel") or "")
    if "models" not in config and {old_model, old_sonnet, old_opus, old_haiku} == {"sonnet"}:
        old_model = old_sonnet = old_opus = old_haiku = ""

    return {
        "baseUrl": str(config.get("baseUrl") or ""),
        "authToken": str(config.get("authToken") or ""),
        "claudeConfigDir": str(config.get("claudeConfigDir") or ""),
        "models": {
            "main": str(models.get("main") or old_model),
            "sonnet": str(models.get("sonnet") or old_sonnet),
            "opus": str(models.get("opus") or old_opus),
            "haiku": str(models.get("haiku") or old_haiku),
        },
        "launch": {
            "settingSources": str(launch.get("settingSources") or config.get("settingSources") or "local"),
            "dangerouslySkipPermissions": bool(launch.get("dangerouslySkipPermissions", config.get("skipPermissions", True))),
            "extraArgs": list(launch.get("extraArgs") or config.get("extraArgs") or []),
        },
        "advanced": {
            "apiTimeoutMs": str(advanced.get("apiTimeoutMs") or config.get("timeoutMs") or "3000000"),
            "usePowershellTool": bool(advanced.get("usePowershellTool", config.get("usePowershellTool", True))),
            "disableNonessentialTraffic": bool(advanced.get("disableNonessentialTraffic", config.get("disableNonessentialTraffic", True))),
            "disableTelemetry": bool(advanced.get("disableTelemetry", config.get("disableTelemetry", False))),
            "disableAutoUpdater": bool(advanced.get("disableAutoUpdater", config.get("disableAutoUpdater", False))),
            "bashDefaultTimeoutMs": str(advanced.get("bashDefaultTimeoutMs") or ""),
            "bashMaxTimeoutMs": str(advanced.get("bashMaxTimeoutMs") or ""),
            "bashMaxOutputLength": str(advanced.get("bashMaxOutputLength") or ""),
            "extraEnv": dict(advanced.get("extraEnv") or config.get("extraEnv") or {}),
        },
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
    models = config.get("models", {})
    launch = config.get("launch", {})
    advanced = config.get("advanced", {})

    lines = claude_script_header(profile)
    lines.extend(
        env_lines(
            {
                "CLAUDE_CONFIG_DIR": config.get("claudeConfigDir", ""),
                "ANTHROPIC_AUTH_TOKEN": config["authToken"],
                "ANTHROPIC_BASE_URL": config["baseUrl"],
            },
            quote=ps_double_quote,
        )
    )

    model_env = {
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": models.get("haiku", ""),
        "ANTHROPIC_DEFAULT_OPUS_MODEL": models.get("opus", ""),
        "ANTHROPIC_DEFAULT_SONNET_MODEL": models.get("sonnet", ""),
        "ANTHROPIC_MODEL": models.get("main", ""),
    }
    if any(str(value) for value in model_env.values()):
        lines.extend(env_lines(model_env, quote=ps_double_quote))

    advanced_env = {
        "API_TIMEOUT_MS": advanced.get("apiTimeoutMs", ""),
    }
    if advanced.get("disableNonessentialTraffic"):
        advanced_env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
    if advanced.get("usePowershellTool"):
        advanced_env["CLAUDE_CODE_USE_POWERSHELL_TOOL"] = "1"
    if advanced.get("disableTelemetry"):
        advanced_env["CLAUDE_CODE_DISABLE_TELEMETRY"] = "1"
    if advanced.get("disableAutoUpdater"):
        advanced_env["CLAUDE_CODE_DISABLE_AUTOUPDATER"] = "1"
    advanced_env.update(
        {
            "BASH_DEFAULT_TIMEOUT_MS": advanced.get("bashDefaultTimeoutMs", ""),
            "BASH_MAX_TIMEOUT_MS": advanced.get("bashMaxTimeoutMs", ""),
            "BASH_MAX_OUTPUT_LENGTH": advanced.get("bashMaxOutputLength", ""),
        }
    )
    advanced_env.update({str(k): str(v) for k, v in advanced.get("extraEnv", {}).items()})
    lines.extend(env_lines(advanced_env, quote=ps_double_quote))

    args = []
    if launch.get("settingSources"):
        args.extend(["--setting-sources", str(launch["settingSources"])])
    if launch.get("dangerouslySkipPermissions"):
        args.append("--dangerously-skip-permissions")
    args.extend(str(arg) for arg in launch.get("extraArgs", []))
    command = "claude" + ps_args(args, quote=ps_arg_quote)
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


def sync_claude_script_to_profile(profile: dict[str, Any], text: str) -> dict[str, Any]:
    next_profile = normalize_profile(profile)
    parsed = parse_ps1(text)
    if parsed["workingDirectory"]:
        next_profile["workingDirectory"] = parsed["workingDirectory"]

    config = next_profile["config"]
    advanced = config["advanced"]
    models = config["models"]
    launch = config["launch"]
    extra_env = dict(advanced.get("extraEnv") or {})

    env_map = {
        "CLAUDE_CONFIG_DIR": ("config", "claudeConfigDir"),
        "ANTHROPIC_AUTH_TOKEN": ("config", "authToken"),
        "ANTHROPIC_BASE_URL": ("config", "baseUrl"),
        "ANTHROPIC_MODEL": ("models", "main"),
        "ANTHROPIC_DEFAULT_SONNET_MODEL": ("models", "sonnet"),
        "ANTHROPIC_DEFAULT_OPUS_MODEL": ("models", "opus"),
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": ("models", "haiku"),
        "API_TIMEOUT_MS": ("advanced", "apiTimeoutMs"),
        "BASH_DEFAULT_TIMEOUT_MS": ("advanced", "bashDefaultTimeoutMs"),
        "BASH_MAX_TIMEOUT_MS": ("advanced", "bashMaxTimeoutMs"),
        "BASH_MAX_OUTPUT_LENGTH": ("advanced", "bashMaxOutputLength"),
    }
    bool_env_map = {
        "CLAUDE_CODE_USE_POWERSHELL_TOOL": "usePowershellTool",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "disableNonessentialTraffic",
        "CLAUDE_CODE_DISABLE_TELEMETRY": "disableTelemetry",
        "CLAUDE_CODE_DISABLE_AUTOUPDATER": "disableAutoUpdater",
    }
    for key, value in parsed["env"].items():
        if key in env_map:
            scope, target = env_map[key]
            if scope == "config":
                config[target] = value
            elif scope == "models":
                models[target] = value
            else:
                advanced[target] = value
        elif key in bool_env_map:
            parsed_bool = parse_bool(value)
            if parsed_bool is not None:
                advanced[bool_env_map[key]] = parsed_bool
        else:
            extra_env[key] = value
    advanced["extraEnv"] = extra_env

    args = parsed["commands"].get("claude")
    if args:
        extra_args = []
        index = 0
        while index < len(args):
            arg = args[index]
            if arg == "--setting-sources" and index + 1 < len(args):
                launch["settingSources"] = args[index + 1]
                index += 2
            elif arg == "--dangerously-skip-permissions":
                launch["dangerouslySkipPermissions"] = True
                index += 1
            else:
                extra_args.append(arg)
                index += 1
        launch["extraArgs"] = extra_args
    return next_profile


def sync_codex_script_to_profile(profile: dict[str, Any], text: str) -> dict[str, Any]:
    next_profile = normalize_profile(profile)
    parsed = parse_ps1(text)
    if parsed["workingDirectory"]:
        next_profile["workingDirectory"] = parsed["workingDirectory"]

    config = next_profile["config"]
    provider = config["provider"]
    extra_env = dict(config.get("extraEnv") or {})
    api_key_env_name = config["apiKeyEnvName"]
    for key, value in parsed["env"].items():
        if key == api_key_env_name:
            config["apiKey"] = value
        else:
            extra_env[key] = value
    config["extraEnv"] = extra_env

    args = parsed["commands"].get("codex")
    if not args:
        return next_profile

    extra_args = []
    extra_config = dict(config.get("extraConfig") or {})
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--ignore-user-config":
            config["ignoreUserConfig"] = True
            index += 1
        elif arg == "-c" and index + 1 < len(args):
            key, value = parse_assignment(args[index + 1])
            if key:
                apply_codex_config_value(config, provider, extra_config, key, value)
            index += 2
        else:
            extra_args.append(arg)
            index += 1
    if config["apiKeyEnvName"] in extra_env:
        config["apiKey"] = str(extra_env.pop(config["apiKeyEnvName"]))
    config["extraArgs"] = extra_args
    config["extraConfig"] = extra_config
    config["extraEnv"] = extra_env
    return next_profile


def apply_codex_config_value(config: dict[str, Any], provider: dict[str, Any], extra_config: dict[str, Any], key: str, value: Any) -> None:
    if key == "model_provider":
        provider["id"] = str(value)
    elif key == "model":
        config["model"] = str(value)
    elif key == "model_reasoning_effort":
        config["reasoningEffort"] = str(value)
    elif key == "disable_response_storage":
        config["disableResponseStorage"] = bool(value)
    elif key == "features.apps":
        config["appsEnabled"] = bool(value)
    elif key.startswith("model_providers.") and key.endswith(".name"):
        provider["name"] = str(value)
    elif key.startswith("model_providers.") and key.endswith(".base_url"):
        provider["baseUrl"] = str(value)
    elif key.startswith("model_providers.") and key.endswith(".env_key"):
        config["apiKeyEnvName"] = str(value)
    elif key.startswith("model_providers.") and key.endswith(".wire_api"):
        provider["wireApi"] = str(value)
    else:
        extra_config[key] = value


def parse_ps1(text: str) -> dict[str, Any]:
    env: dict[str, str] = {}
    commands: dict[str, list[str]] = {}
    working_directory = ""
    for line in join_ps_continuations(text).splitlines():
        stripped = strip_ps_comment(line).strip()
        if not stripped:
            continue
        location = parse_location_line(stripped)
        if location:
            working_directory = location
            continue
        env_match = re.match(r"^\$env:([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$", stripped)
        if env_match:
            env[env_match.group(1)] = parse_ps_value(env_match.group(2))
            continue
        tokens = ps_tokenize(stripped)
        if tokens and tokens[0].lower() in {"claude", "codex"}:
            commands[tokens[0].lower()] = tokens[1:]
    return {"workingDirectory": working_directory, "env": env, "commands": commands}


def join_ps_continuations(text: str) -> str:
    lines = []
    current = ""
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.endswith("`"):
            current += line[:-1] + " "
        else:
            lines.append(current + line)
            current = ""
    if current:
        lines.append(current)
    return "\n".join(lines)


def strip_ps_comment(line: str) -> str:
    in_single = False
    in_double = False
    index = 0
    while index < len(line):
        ch = line[index]
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            return line[:index]
        index += 1
    return line


def parse_location_line(line: str) -> str:
    tokens = ps_tokenize(line)
    if len(tokens) >= 2 and tokens[0].lower() in {"cd", "set-location"}:
        return tokens[1]
    return ""


def parse_ps_value(value: str) -> str:
    tokens = ps_tokenize(value)
    return tokens[0] if tokens else value.strip()


def ps_tokenize(line: str) -> list[str]:
    tokens: list[str] = []
    current = ""
    quote = ""
    index = 0
    while index < len(line):
        ch = line[index]
        if quote:
            if quote == '"' and ch == "`" and index + 1 < len(line):
                current += line[index + 1]
                index += 2
                continue
            if ch == quote:
                quote = ""
            else:
                current += ch
        else:
            if ch in {"'", '"'}:
                quote = ch
            elif ch.isspace():
                if current:
                    tokens.append(current)
                    current = ""
            else:
                current += ch
        index += 1
    if current:
        tokens.append(current)
    return tokens


def parse_bool(value: Any) -> bool | None:
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off", ""}:
        return False
    return None


def parse_assignment(value: str) -> tuple[str, Any]:
    if "=" not in value:
        return "", ""
    key, raw = value.split("=", 1)
    return key.strip(), parse_toml_scalar(raw.strip())


def parse_toml_scalar(value: str) -> Any:
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(value)
    except ValueError:
        return value


def claude_script_header(profile: dict[str, Any]) -> list[str]:
    return [
        f"# Generated by MulCat from profiles/{profile['kind']}/{profile['id']}.json",
        f"cd {ps_double_quote(profile['workingDirectory'])}",
        "",
    ]


def script_header(profile: dict[str, Any]) -> list[str]:
    return [
        f"# Generated by MulCat from profiles/{profile['kind']}/{profile['id']}.json",
        "$ErrorActionPreference = 'Stop'",
        f"Set-Location {ps_quote(profile['workingDirectory'])}",
        "",
    ]


def env_lines(env: dict[str, str], quote=None) -> list[str]:
    if quote is None:
        quote = ps_quote
    lines = []
    for key, value in env.items():
        if value != "":
            lines.append(f"$env:{key} = {quote(value)}")
    lines.append("")
    return lines


def ps_quote(value: Any) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def ps_double_quote(value: Any) -> str:
    return '"' + str(value).replace("`", "``").replace('"', '`"') + '"'


def ps_arg_quote(value: Any) -> str:
    text = str(value)
    if text and all(ch not in text for ch in " \t\r\n\"'`"):
        return text
    return ps_double_quote(text)


def ps_args(args: list[str], quote=ps_quote) -> str:
    if not args:
        return ""
    return " " + " ".join(quote(arg) for arg in args)


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

