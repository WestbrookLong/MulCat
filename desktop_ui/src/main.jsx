import React from "react";
import { createRoot } from "react-dom/client";
import {
  Bot,
  ChevronDown,
  ChevronRight,
  Code2,
  CopyPlus,
  Eye,
  EyeOff,
  FileCode2,
  FolderOpen,
  Play,
  Plus,
  RefreshCw,
  Save,
  TerminalSquare,
  Trash2,
  X,
} from "lucide-react";
import "./styles.css";

const defaultWorkdir = "D:\\AIWorkspace";

const claudeProviders = [
  {
    id: "claude-relay",
    name: "Claude 中转",
    description: "适合 Anthropic 兼容中转，不预设模型环境变量。",
    profileName: "Claude 中转",
    config: {
      baseUrl: "https://lingsuan.top",
      authToken: "",
      models: { main: "", sonnet: "", opus: "", haiku: "" },
      launch: { settingSources: "local", dangerouslySkipPermissions: true, extraArgs: [] },
      advanced: {
        apiTimeoutMs: "3000000",
        disableNonessentialTraffic: true,
        usePowershellTool: true,
        disableTelemetry: false,
        disableAutoUpdater: false,
        bashDefaultTimeoutMs: "",
        bashMaxTimeoutMs: "",
        bashMaxOutputLength: "",
        extraEnv: {},
      },
    },
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    description: "预设 DeepSeek Anthropic 兼容地址和模型映射。",
    profileName: "DeepSeek",
    config: {
      baseUrl: "https://api.deepseek.com/anthropic",
      authToken: "",
      models: {
        main: "deepseek-v4-pro",
        sonnet: "deepseek-v4-pro",
        opus: "deepseek-v4-pro",
        haiku: "deepseek-v4-flash",
      },
      launch: { settingSources: "local", dangerouslySkipPermissions: true, extraArgs: [] },
      advanced: {
        apiTimeoutMs: "3000000",
        disableNonessentialTraffic: true,
        usePowershellTool: true,
        disableTelemetry: false,
        disableAutoUpdater: false,
        bashDefaultTimeoutMs: "",
        bashMaxTimeoutMs: "",
        bashMaxOutputLength: "",
        extraEnv: {},
      },
    },
  },
];

const templates = {
  claude: {
    id: "claude-new",
    name: "Claude New",
    kind: "claude",
    provider: "",
    enabled: true,
    workingDirectory: defaultWorkdir,
    terminal: { mode: "windows-terminal", keepOpen: true },
    config: clone(claudeProviders[0].config),
  },
  codex: {
    id: "codex-new",
    name: "Codex New",
    kind: "codex",
    enabled: true,
    workingDirectory: defaultWorkdir,
    terminal: { mode: "windows-terminal", keepOpen: true },
    config: {
      ignoreUserConfig: true,
      apiKeyEnvName: "OPENAI_API_KEY",
      apiKey: "",
      provider: {
        id: "custom",
        name: "Custom",
        baseUrl: "",
        wireApi: "responses",
      },
      model: "gpt-5",
      reasoningEffort: "high",
      disableResponseStorage: true,
      appsEnabled: false,
      extraEnv: {},
      extraConfig: {},
      extraArgs: [],
    },
  },
};

function desktopApi() {
  return window.pywebview?.api;
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function App() {
  const [state, setState] = React.useState({ profiles: [], message: "", appDir: "", scriptsDir: "" });
  const [filter, setFilter] = React.useState("claude");
  const [selectedKey, setSelectedKey] = React.useState("");
  const [draft, setDraft] = React.useState(null);
  const [configOpen, setConfigOpen] = React.useState(false);
  const [providerOpen, setProviderOpen] = React.useState(false);
  const [scriptModal, setScriptModal] = React.useState({ open: false, path: "", text: "", profile: null });
  const [localMessage, setLocalMessage] = React.useState("");

  const profiles = state.profiles || [];
  const filtered = profiles.filter((profile) => profile.kind === filter);
  const selected = filtered.find((profile) => keyOf(profile) === selectedKey) || filtered[0] || null;

  const refresh = React.useCallback(async () => {
    const api = desktopApi();
    if (!api) return;
    const next = await api.get_state();
    setState(next);
    if (!selectedKey && next.profiles?.length) {
      const first = next.profiles.find((profile) => profile.kind === filter) || next.profiles[0];
      setSelectedKey(keyOf(first));
    }
  }, [filter, selectedKey]);

  React.useEffect(() => {
    const ready = () => refresh();
    window.addEventListener("pywebviewready", ready);
    refresh();
    return () => window.removeEventListener("pywebviewready", ready);
  }, [refresh]);

  React.useEffect(() => {
    if (selected) setSelectedKey(keyOf(selected));
  }, [filter, selected]);

  async function callApi(action, ...args) {
    const api = desktopApi();
    if (!api) {
      setLocalMessage("Desktop API 尚未就绪。");
      return null;
    }
    try {
      const result = await api[action](...args);
      setState(result);
      setLocalMessage(result.message || "");
      return result;
    } catch (error) {
      setLocalMessage(`Desktop API error: ${error?.message || error}`);
      return null;
    }
  }

  async function chooseDirectory(initialDirectory) {
    const result = await callApi("choose_directory", initialDirectory || defaultWorkdir);
    return result?.selectedDirectory || "";
  }

  function openConfig(profile) {
    setDraft(clone(profile));
    setConfigOpen(true);
  }

  function newProfile() {
    if (filter === "claude") {
      setProviderOpen(true);
      return;
    }
    const next = withUniqueId(clone(templates.codex), "codex", "Codex");
    setDraft(next);
    setConfigOpen(true);
  }

  function newClaudeProfile(provider) {
    const next = withUniqueId(clone(templates.claude), "claude", provider.profileName);
    next.provider = provider.id;
    next.config = clone(provider.config);
    setProviderOpen(false);
    setDraft(next);
    setConfigOpen(true);
  }

  function duplicateProfile(profile) {
    const next = clone(profile);
    const suffix = Date.now().toString().slice(-5);
    next.id = `${profile.id}-copy-${suffix}`;
    next.name = `${profile.name} Copy`;
    setDraft(next);
    setConfigOpen(true);
  }

  async function saveDraft() {
    if (!draft) return;
    const result = await callApi("save_profile", draft);
    const saved = result?.profiles?.find((profile) => profile.id === draft.id && profile.kind === draft.kind);
    if (saved) {
      setSelectedKey(keyOf(saved));
      setConfigOpen(false);
    }
  }

  async function openScript(profile) {
    const result = await callApi("read_script", profile.kind, profile.id);
    setScriptModal({
      open: true,
      path: result?.scriptPath || profile._scriptPath || "",
      text: result?.scriptText || "",
      profile,
    });
  }

  async function saveScript() {
    if (!scriptModal.profile) return;
    await callApi("save_script", scriptModal.profile.kind, scriptModal.profile.id, scriptModal.text);
    setScriptModal({ open: false, path: "", text: "", profile: null });
  }

  const displayMessage = localMessage || state.message || "Ready";

  return (
    <div className="flex h-screen overflow-hidden bg-black text-white">
      <div className="relative flex min-h-0 w-full flex-col">
        <TitleBar />

        <main className="grid min-h-0 flex-1 grid-cols-[220px_1fr] gap-px bg-zinc-800">
          <aside className="flex min-h-0 flex-col bg-black">
            <div className="border-b border-zinc-800 px-4 py-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <TerminalSquare size={17} />
                MulCat
              </div>
              <div className="mt-1 font-mono text-[11px] text-zinc-500">JSON to PS1</div>
            </div>

            <nav className="space-y-1 p-3">
              <FilterButton active={filter === "claude"} icon={Bot} label="Claude" count={profiles.filter((p) => p.kind === "claude").length} onClick={() => setFilter("claude")} />
              <FilterButton active={filter === "codex"} icon={TerminalSquare} label="Codex" count={profiles.filter((p) => p.kind === "codex").length} onClick={() => setFilter("codex")} />
            </nav>

            <div className="mt-auto border-t border-zinc-800 p-3">
              <IconButton icon={FolderOpen} label="脚本目录" onClick={() => callApi("open_scripts_dir")} />
              <IconButton icon={RefreshCw} label="重新生成 PS1" onClick={() => callApi("generate_all")} />
            </div>
          </aside>

          <section className="flex min-h-0 flex-col bg-zinc-950">
            <div className="flex items-center justify-between border-b border-zinc-800 px-5 py-4">
              <div>
                <div className="text-base font-semibold text-white">{filter === "claude" ? "Claude 配置" : "Codex 配置"}</div>
                <div className="mt-1 font-mono text-[11px] text-zinc-500">{filtered.length} profiles</div>
              </div>
              <button
                type="button"
                onClick={newProfile}
                className="grid h-9 w-9 place-items-center rounded-sm border border-zinc-700 bg-black text-zinc-200 transition hover:border-white hover:text-white"
                title={`新增 ${filter === "claude" ? "Claude" : "Codex"} 配置`}
              >
                <Plus size={17} />
              </button>
            </div>

            <div className="scroll-surface min-h-0 flex-1 overflow-auto p-4">
              <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
                {filtered.map((profile) => (
                  <ProfileCard
                    key={keyOf(profile)}
                    profile={profile}
                    active={selectedKey === keyOf(profile)}
                    onSelect={() => {
                      setSelectedKey(keyOf(profile));
                      openConfig(profile);
                    }}
                    onLaunch={() => callApi("launch_profile", profile.kind, profile.id)}
                    onScript={() => openScript(profile)}
                    onDuplicate={() => duplicateProfile(profile)}
                  />
                ))}
              </div>
              {!filtered.length && <div className="px-3 py-12 text-center text-sm text-zinc-500">暂无配置，点击右上角加号创建</div>}
            </div>

            <footer className="flex h-10 items-center gap-3 border-t border-zinc-800 px-5 font-mono text-[11px] text-zinc-400">
              <span className="h-2 w-2 rounded-full bg-white" />
              <span className="truncate">{displayMessage}</span>
            </footer>
          </section>
        </main>
      </div>

      {providerOpen && <ProviderModal providers={claudeProviders} onSelect={newClaudeProfile} onClose={() => setProviderOpen(false)} />}

      {configOpen && draft && (
        <ConfigModal
          draft={draft}
          setDraft={setDraft}
          chooseDirectory={chooseDirectory}
          onClose={() => setConfigOpen(false)}
          onSave={saveDraft}
          onDelete={async () => {
            await callApi("delete_profile", draft.kind, draft.id);
            setConfigOpen(false);
          }}
        />
      )}

      {scriptModal.open && (
        <ScriptModal
          path={scriptModal.path}
          text={scriptModal.text}
          setText={(text) => setScriptModal((current) => ({ ...current, text }))}
          onClose={() => setScriptModal({ open: false, path: "", text: "", profile: null })}
          onSave={saveScript}
        />
      )}
    </div>
  );
}

function ProviderModal({ providers, onSelect, onClose }) {
  return (
    <Modal title="选择 Provider" onClose={onClose} compact>
      <div className="grid gap-3">
        {providers.map((provider) => (
          <button
            key={provider.id}
            type="button"
            onClick={() => onSelect(provider)}
            className="rounded-md border border-zinc-800 bg-zinc-950 p-4 text-left transition hover:border-white"
          >
            <div className="text-sm font-semibold text-white">{provider.name}</div>
            <div className="mt-2 text-xs leading-5 text-zinc-400">{provider.description}</div>
            <div className="mt-3 font-mono text-[11px] text-zinc-500">{provider.config.baseUrl}</div>
          </button>
        ))}
      </div>
    </Modal>
  );
}

function ConfigModal({ draft, setDraft, chooseDirectory, onClose, onSave, onDelete }) {
  const set = (path, value) => {
    setDraft((current) => {
      const next = clone(current);
      assignPath(next, path, value);
      return next;
    });
  };

  return (
    <Modal title={`${draft.kind === "claude" ? "Claude" : "Codex"} / ${draft.name}`} onClose={onClose}>
      <div className="scroll-surface max-h-[calc(100vh-180px)] overflow-auto pr-1">
        <div className="space-y-5">
          <Panel title="基础">
            <div className="grid grid-cols-2 gap-3">
              <Field label="ID" value={draft.id} onChange={(value) => set("id", slugify(value))} />
              <Field label="名称" value={draft.name} onChange={(value) => set("name", value)} />
              <Field label="类型" value={draft.kind} readOnly />
              <Toggle label="启用" checked={draft.enabled} onChange={(value) => set("enabled", value)} />
              <Field
                label="工作目录"
                value={draft.workingDirectory}
                onChange={(value) => set("workingDirectory", value)}
                actionIcon={FolderOpen}
                actionTitle="选择目录"
                onAction={async () => {
                  const selected = await chooseDirectory(draft.workingDirectory);
                  if (selected) set("workingDirectory", selected);
                }}
                wide
              />
            </div>
          </Panel>

          {draft.kind === "claude" ? <ClaudeEditor draft={draft} set={set} /> : <CodexEditor draft={draft} set={set} />}
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between border-t border-zinc-800 pt-4">
        <button onClick={onDelete} className="inline-flex h-9 items-center gap-2 rounded-sm border border-zinc-700 bg-black px-3 text-sm text-zinc-300 transition hover:border-white hover:text-white">
          <Trash2 size={15} />
          删除
        </button>
        <div className="flex gap-2">
          <ActionButton icon={X} label="取消" onClick={onClose} />
          <ActionButton icon={Save} label="保存并生成 PS1" onClick={onSave} primary />
        </div>
      </div>
    </Modal>
  );
}

function ScriptModal({ path, text, setText, onClose, onSave }) {
  return (
    <Modal title="直接编辑 PS1" onClose={onClose} wide>
      <div className="mb-2 truncate font-mono text-[11px] text-zinc-500">{path}</div>
      <textarea
        value={text}
        onChange={(event) => setText(event.target.value)}
        spellCheck={false}
        className="h-[58vh] w-full resize-none rounded-sm border border-zinc-700 bg-black px-3 py-3 font-mono text-xs leading-5 text-white outline-none transition focus:border-white"
      />
      <div className="mt-4 flex justify-end gap-2 border-t border-zinc-800 pt-4">
        <ActionButton icon={X} label="取消" onClick={onClose} />
        <ActionButton icon={Save} label="保存 PS1" onClick={onSave} primary />
      </div>
    </Modal>
  );
}

function ClaudeEditor({ draft, set }) {
  const c = ensureClaudeConfig(draft.config);
  return (
    <>
      <Panel title="Claude">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Base URL" value={c.baseUrl} onChange={(value) => set("config.baseUrl", value)} wide />
          <SecretField label="Auth Token" value={c.authToken} onChange={(value) => set("config.authToken", value)} wide />
          <Field label="ANTHROPIC_MODEL" value={c.models.main} onChange={(value) => set("config.models.main", value)} />
          <Field label="ANTHROPIC_DEFAULT_SONNET_MODEL" value={c.models.sonnet} onChange={(value) => set("config.models.sonnet", value)} />
          <Field label="ANTHROPIC_DEFAULT_OPUS_MODEL" value={c.models.opus} onChange={(value) => set("config.models.opus", value)} />
          <Field label="ANTHROPIC_DEFAULT_HAIKU_MODEL" value={c.models.haiku} onChange={(value) => set("config.models.haiku", value)} />
        </div>
      </Panel>

      <Panel title="启动选项">
        <div className="grid grid-cols-2 gap-3">
          <SelectField label="--setting-sources" value={c.launch.settingSources} options={["local", "user", "project"]} onChange={(value) => set("config.launch.settingSources", value)} />
          <Toggle label="--dangerously-skip-permissions" checked={c.launch.dangerouslySkipPermissions} onChange={(value) => set("config.launch.dangerouslySkipPermissions", value)} />
          <ArrayField label="Extra Args" value={c.launch.extraArgs || []} onChange={(value) => set("config.launch.extraArgs", value)} />
        </div>
      </Panel>

      <AdvancedClaudePanel config={c} set={set} />
    </>
  );
}

function AdvancedClaudePanel({ config, set }) {
  const [open, setOpen] = React.useState(false);
  const a = config.advanced;
  return (
    <section className="rounded-md border border-zinc-800 bg-zinc-950">
      <button type="button" onClick={() => setOpen((value) => !value)} className="flex w-full items-center justify-between border-b border-zinc-800 px-4 py-2 text-left">
        <span className="text-xs font-semibold uppercase tracking-wide text-zinc-400">高级设置</span>
        {open ? <ChevronDown size={15} className="text-zinc-400" /> : <ChevronRight size={15} className="text-zinc-400" />}
      </button>
      {open && (
        <div className="space-y-4 p-4">
          <div className="grid grid-cols-2 gap-3">
            <Field label="API_TIMEOUT_MS" value={a.apiTimeoutMs} onChange={(value) => set("config.advanced.apiTimeoutMs", value)} />
            <Toggle label="CLAUDE_CODE_USE_POWERSHELL_TOOL" checked={a.usePowershellTool} onChange={(value) => set("config.advanced.usePowershellTool", value)} />
            <Toggle label="CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC" checked={a.disableNonessentialTraffic} onChange={(value) => set("config.advanced.disableNonessentialTraffic", value)} />
            <Toggle label="CLAUDE_CODE_DISABLE_TELEMETRY" checked={a.disableTelemetry} onChange={(value) => set("config.advanced.disableTelemetry", value)} />
            <Toggle label="CLAUDE_CODE_DISABLE_AUTOUPDATER" checked={a.disableAutoUpdater} onChange={(value) => set("config.advanced.disableAutoUpdater", value)} />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <Field label="BASH_DEFAULT_TIMEOUT_MS" value={a.bashDefaultTimeoutMs} onChange={(value) => set("config.advanced.bashDefaultTimeoutMs", value)} />
            <Field label="BASH_MAX_TIMEOUT_MS" value={a.bashMaxTimeoutMs} onChange={(value) => set("config.advanced.bashMaxTimeoutMs", value)} />
            <Field label="BASH_MAX_OUTPUT_LENGTH" value={a.bashMaxOutputLength} onChange={(value) => set("config.advanced.bashMaxOutputLength", value)} />
          </div>
          <JsonField label="Extra Env" value={a.extraEnv || {}} onChange={(value) => set("config.advanced.extraEnv", value)} />
        </div>
      )}
    </section>
  );
}

function CodexEditor({ draft, set }) {
  const c = draft.config;
  return (
    <>
      <Panel title="Codex">
        <div className="grid grid-cols-2 gap-3">
          <Field label="API Key Env" value={c.apiKeyEnvName} onChange={(value) => set("config.apiKeyEnvName", value)} />
          <SecretField label="API Key" value={c.apiKey} onChange={(value) => set("config.apiKey", value)} />
          <Field label="model_provider" value={c.provider.id} onChange={(value) => set("config.provider.id", slugify(value) || "custom")} />
          <Field label="Provider Name" value={c.provider.name} onChange={(value) => set("config.provider.name", value)} />
          <Field label="base_url" value={c.provider.baseUrl} onChange={(value) => set("config.provider.baseUrl", value)} wide />
          <SelectField label="wire_api" value={c.provider.wireApi} options={["responses", "chat"]} onChange={(value) => set("config.provider.wireApi", value)} />
          <Field label="model" value={c.model} onChange={(value) => set("config.model", value)} />
          <SelectField label="model_reasoning_effort" value={c.reasoningEffort} options={["minimal", "low", "medium", "high"]} onChange={(value) => set("config.reasoningEffort", value)} />
          <Toggle label="--ignore-user-config" checked={c.ignoreUserConfig} onChange={(value) => set("config.ignoreUserConfig", value)} />
          <Toggle label="disable_response_storage" checked={c.disableResponseStorage} onChange={(value) => set("config.disableResponseStorage", value)} />
          <Toggle label="features.apps" checked={c.appsEnabled} onChange={(value) => set("config.appsEnabled", value)} />
        </div>
      </Panel>
      <Panel title="高级">
        <div className="grid grid-cols-2 gap-3">
          <JsonField label="Extra Env" value={c.extraEnv || {}} onChange={(value) => set("config.extraEnv", value)} />
          <JsonField label="Extra Config (-c)" value={c.extraConfig || {}} onChange={(value) => set("config.extraConfig", value)} />
          <ArrayField label="Extra Args" value={c.extraArgs || []} onChange={(value) => set("config.extraArgs", value)} />
        </div>
      </Panel>
    </>
  );
}

function ProfileCard({ profile, active, onSelect, onLaunch, onScript, onDuplicate }) {
  const Icon = profile.kind === "claude" ? Bot : TerminalSquare;
  return (
    <article className={`rounded-lg border p-4 transition ${active ? "border-white bg-zinc-900" : "border-zinc-800 bg-black hover:border-zinc-500"}`}>
      <button type="button" onClick={onSelect} className="block w-full text-left">
        <div className="flex items-start gap-3">
          <div className="grid h-9 w-9 shrink-0 place-items-center rounded-md border border-zinc-700 bg-zinc-950">
            <Icon size={17} className="text-zinc-200" />
          </div>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold text-white">{profile.name}</div>
            <div className="mt-1 truncate font-mono text-[11px] text-zinc-500">{profile.id}</div>
            <div className="mt-2 truncate text-xs text-zinc-400">{summary(profile)}</div>
          </div>
        </div>
      </button>
      <div className="mt-4 flex items-center justify-end gap-2 border-t border-zinc-800 pt-3">
        <SmallIconButton icon={CopyPlus} title="复制配置" onClick={onDuplicate} />
        <SmallIconButton icon={FileCode2} title="编辑 PS1" onClick={onScript} />
        <SmallIconButton icon={Play} title="启动" onClick={onLaunch} strong />
      </div>
    </article>
  );
}

function Modal({ title, onClose, children, wide, compact }) {
  const width = compact ? "max-w-lg" : wide ? "max-w-5xl" : "max-w-4xl";
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 px-5 py-5">
      <div className={`max-h-full w-full rounded-xl border border-zinc-700 bg-black shadow-2xl ${width}`}>
        <div className="flex h-12 items-center justify-between border-b border-zinc-800 px-4">
          <div className="truncate text-sm font-semibold text-white">{title}</div>
          <button onClick={onClose} className="grid h-8 w-8 place-items-center rounded-sm border border-zinc-700 text-zinc-300 hover:border-white hover:text-white" title="关闭">
            <X size={16} />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

function Panel({ title, children }) {
  return (
    <section className="rounded-md border border-zinc-800 bg-zinc-950">
      <div className="border-b border-zinc-800 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-zinc-400">{title}</div>
      <div className="p-4">{children}</div>
    </section>
  );
}

function Field({ label, value, onChange, readOnly, wide, actionIcon: ActionIcon, actionTitle, onAction }) {
  return (
    <label className={wide ? "col-span-2 block" : "block"}>
      <span className="mb-1 block text-xs text-zinc-400">{label}</span>
      <div className="flex h-9 rounded-sm border border-zinc-700 bg-black transition focus-within:border-white">
        <input
          type="text"
          value={value ?? ""}
          readOnly={readOnly}
          onChange={(event) => onChange?.(event.target.value)}
          className="min-w-0 flex-1 bg-transparent px-3 text-sm text-white outline-none read-only:text-zinc-500"
        />
        {ActionIcon && (
          <button type="button" onClick={onAction} className="grid w-9 place-items-center text-zinc-400 hover:text-white" title={actionTitle}>
            <ActionIcon size={15} />
          </button>
        )}
      </div>
    </label>
  );
}

function SecretField({ label, value, onChange, wide }) {
  const [visible, setVisible] = React.useState(false);
  return (
    <label className={wide ? "col-span-2 block" : "block"}>
      <span className="mb-1 block text-xs text-zinc-400">{label}</span>
      <div className="flex h-9 rounded-sm border border-zinc-700 bg-black transition focus-within:border-white">
        <input
          type={visible ? "text" : "password"}
          value={value ?? ""}
          onChange={(event) => onChange(event.target.value)}
          className="min-w-0 flex-1 bg-transparent px-3 text-sm text-white outline-none"
        />
        <button type="button" onClick={() => setVisible((next) => !next)} className="grid w-9 place-items-center text-zinc-400 hover:text-white" title={visible ? "隐藏" : "显示"}>
          {visible ? <EyeOff size={15} /> : <Eye size={15} />}
        </button>
      </div>
    </label>
  );
}

function SelectField({ label, value, options, onChange }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs text-zinc-400">{label}</span>
      <select
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value)}
        className="h-9 w-full rounded-sm border border-zinc-700 bg-black px-3 text-sm text-white outline-none transition focus:border-white"
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function Toggle({ label, checked, onChange }) {
  return (
    <label className="flex h-9 items-center justify-between gap-3 rounded-sm border border-zinc-700 bg-black px-3">
      <span className="truncate text-sm text-zinc-300">{label}</span>
      <input type="checkbox" checked={!!checked} onChange={(event) => onChange(event.target.checked)} className="h-4 w-4 shrink-0 accent-white" />
    </label>
  );
}

function JsonField({ label, value, onChange }) {
  const [text, setText] = React.useState(JSON.stringify(value || {}, null, 2));
  React.useEffect(() => setText(JSON.stringify(value || {}, null, 2)), [JSON.stringify(value || {})]);
  return (
    <label className="col-span-2 block">
      <span className="mb-1 block text-xs text-zinc-400">{label}</span>
      <textarea
        value={text}
        onChange={(event) => {
          const next = event.target.value;
          setText(next);
          try {
            onChange(JSON.parse(next || "{}"));
          } catch {
            return;
          }
        }}
        rows={5}
        spellCheck={false}
        className="w-full resize-y rounded-sm border border-zinc-700 bg-black px-3 py-2 font-mono text-xs leading-5 text-white outline-none transition focus:border-white"
      />
    </label>
  );
}

function ArrayField({ label, value, onChange }) {
  return (
    <label className="col-span-2 block">
      <span className="mb-1 block text-xs text-zinc-400">{label}</span>
      <input
        value={(value || []).join(" ")}
        onChange={(event) => onChange(event.target.value.split(" ").map((x) => x.trim()).filter(Boolean))}
        className="h-9 w-full rounded-sm border border-zinc-700 bg-black px-3 font-mono text-xs text-white outline-none transition focus:border-white"
      />
    </label>
  );
}

function FilterButton({ active, icon: Icon, label, count, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`flex h-10 w-full items-center justify-between rounded-sm border px-3 text-sm transition ${
        active ? "border-white bg-zinc-900 text-white" : "border-transparent text-zinc-400 hover:bg-zinc-900 hover:text-white"
      }`}
    >
      <span className="flex items-center gap-2">
        <Icon size={16} />
        {label}
      </span>
      <span className="font-mono text-xs">{count}</span>
    </button>
  );
}

function IconButton({ icon: Icon, label, onClick }) {
  return (
    <button onClick={onClick} className="mb-2 flex h-9 w-full items-center gap-2 rounded-sm border border-zinc-700 bg-black px-3 text-sm text-zinc-300 transition hover:border-white hover:text-white">
      <Icon size={15} />
      {label}
    </button>
  );
}

function SmallIconButton({ icon: Icon, title, onClick, strong }) {
  return (
    <button
      type="button"
      onClick={(event) => {
        event.stopPropagation();
        onClick();
      }}
      className={`grid h-8 w-8 place-items-center rounded-sm border transition ${
        strong ? "border-white bg-white text-black hover:bg-zinc-200" : "border-zinc-700 bg-black text-zinc-300 hover:border-white hover:text-white"
      }`}
      title={title}
    >
      <Icon size={15} />
    </button>
  );
}

function ActionButton({ icon: Icon, label, onClick, disabled, primary }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex h-9 items-center gap-2 rounded-sm border px-3 text-sm transition disabled:cursor-not-allowed disabled:opacity-45 ${
        primary ? "border-white bg-white text-black hover:bg-zinc-200" : "border-zinc-700 bg-black text-zinc-300 hover:border-white hover:text-white"
      }`}
    >
      <Icon size={15} />
      {label}
    </button>
  );
}

function TitleBar() {
  return (
    <div className="relative z-20 flex h-10 shrink-0 items-center border-b border-zinc-800 bg-black px-4">
      <Code2 size={16} className="text-white" />
      <div className="ml-2 font-mono text-[11px] uppercase tracking-[0.22em] text-zinc-300">MulCat</div>
    </div>
  );
}

function withUniqueId(profile, kind, name) {
  const suffix = Date.now().toString().slice(-5);
  profile.id = `${kind}-${suffix}`;
  profile.name = `${name} ${suffix}`;
  return profile;
}

function keyOf(profile) {
  return `${profile.kind}:${profile.id}`;
}

function summary(profile) {
  if (profile.kind === "claude") {
    const model = profile.config?.models?.main || "未设置模型";
    return `${model} / ${profile.config?.baseUrl || "no base url"}`;
  }
  return `${profile.config.model || "model"} / ${profile.config.provider?.name || "provider"}`;
}

function ensureClaudeConfig(config) {
  return {
    ...config,
    models: config.models || { main: "", sonnet: "", opus: "", haiku: "" },
    launch: config.launch || { settingSources: "local", dangerouslySkipPermissions: true, extraArgs: [] },
    advanced: config.advanced || {
      apiTimeoutMs: "3000000",
      usePowershellTool: true,
      disableNonessentialTraffic: true,
      disableTelemetry: false,
      disableAutoUpdater: false,
      bashDefaultTimeoutMs: "",
      bashMaxTimeoutMs: "",
      bashMaxOutputLength: "",
      extraEnv: {},
    },
  };
}

function assignPath(target, path, value) {
  const keys = path.split(".");
  let cursor = target;
  for (let index = 0; index < keys.length - 1; index += 1) {
    const key = keys[index];
    if (!cursor[key] || typeof cursor[key] !== "object") cursor[key] = {};
    cursor = cursor[key];
  }
  cursor[keys[keys.length - 1]] = value;
}

function slugify(value) {
  return String(value || "")
    .trim()
    .replace(/\s+/g, "-")
    .replace(/[^A-Za-z0-9_-]/g, "")
    .toLowerCase();
}

createRoot(document.getElementById("root")).render(<App />);
