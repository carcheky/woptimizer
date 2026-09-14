import { readFile, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { spawn, execFile } from 'node:child_process';
import { join } from 'node:path';

const SAVED_FILE = 'saved_processes.json';
const PS_DELIM = '\t';
const MAX_CMDLINE_LEN = 4000;

const PROCESS_CATEGORIES = {
  '🔴 Navegadores': { priority: 'high', patterns: ['chrome', 'firefox', 'msedge', 'brave', 'opera', 'vivaldi', 'iexplore', 'chromium', 'arc'] },
  '🔴 Sincronización': { priority: 'high', patterns: ['onedrive', 'dropbox', 'googledrive', 'megasync', 'icloud', 'nextcloud', 'resilio', 'syncthing'] },
  '🟡 Chat y Comunicación': { priority: 'medium', patterns: ['discord', 'slack', 'teams', 'telegram', 'skype', 'whatsapp', 'zoom', 'signal'] },
  '🟡 Productividad': { priority: 'medium', patterns: ['office', 'winword', 'excel', 'outlook', 'notion', 'obsidian', 'adobe', 'photoshop'] },
  '🟡 Media': { priority: 'medium', patterns: ['spotify', 'itunes', 'foobar2000', 'vlc', 'mpv', 'audacity'] },
  '🟢 Overlays / Streaming': { priority: 'low', patterns: ['obs', 'streamlabs', 'geforce', 'radeon', 'rtx', 'rtss', 'afterburner', 'rivatuner'] },
  '🟢 Launchers / Anti-cheat': { priority: 'low', patterns: ['steam', 'epicgames', 'origin', 'eadesktop', 'battle.net', 'ubisoft', 'gog'] },
  '⚫ Antivirus / Seguridad': { priority: 'none', patterns: ['defender', 'antivirus', 'avast', 'avg', 'bitdefender', 'norton', 'malwarebytes', 'mcafee', 'eset'] },
  '⚫ Sistema': { priority: 'none', patterns: ['svchost', 'csrss', 'lsass', 'winlogon', 'dwm', 'services', 'smss', 'wininit'] },
};

const CATEGORY_ORDER = Object.keys(PROCESS_CATEGORIES);
const SIMPLE_CATEGORIES = ['🔴 Navegadores', '🔴 Sincronización', '🟡 Chat y Comunicación', '🟡 Productividad', '🟡 Media'];

function categorize(name) {
  const lower = name.toLowerCase();
  for (const cat of CATEGORY_ORDER) {
    for (const pat of PROCESS_CATEGORIES[cat].patterns) {
      if (lower.includes(pat)) return cat;
    }
  }
  return '⚪ Otros';
}

function runPowershell(script) {
  return new Promise((resolve, reject) => {
    const args = ['-NoProfile', '-NonInteractive', '-Command', script];
    const child = spawn('powershell.exe', args, { windowsHide: true });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (d) => { stdout += d.toString('utf8'); });
    child.stderr.on('data', (d) => { stderr += d.toString('utf8'); });
    child.on('error', reject);
    child.on('close', (code) => {
      if (code !== 0) reject(new Error(`PowerShell exit ${code}: ${stderr.slice(0, 200)}`));
      else resolve(stdout);
    });
  });
}

async function listProcesses() {
  const ps = `
$ProgressPreference = 'SilentlyContinue'
$OutputEncoding = [System.Text.Encoding]::UTF8
Get-CimInstance Win32_Process |
    Where-Object { $_.Name -notin @('powershell.exe', 'pwsh.exe') -and $_.CommandLine } |
    ForEach-Object {
        $name = $_.Name
        $pid = $_.ProcessId
        $memMB = 0
        if ($_.WorkingSetSize -and $_.WorkingSetSize -gt 0) {
            $memMB = [math]::Round($_.WorkingSetSize / 1MB, 1)
        }
        $cmd = $_.CommandLine -replace "[\\t\\r\\n]", ' '
        if ($cmd.Length -gt ${MAX_CMDLINE_LEN}) {
            $cmd = $cmd.Substring(0, ${MAX_CMDLINE_LEN}) + "...[truncated]"
        }
        Write-Output "$name\`t$pid\`t$memMB\`t$cmd"
    }
`;
  const out = await runPowershell(ps);
  const procs = [];
  for (const line of out.split(/\r?\n/)) {
    if (!line.trim()) continue;
    const parts = line.split(PS_DELIM);
    if (parts.length < 4) continue;
    const [name, pidStr, memStr, ...cmdParts] = parts;
    const cmdline = cmdParts.join(PS_DELIM);
    const pid = String(pidStr).trim();
    const memMB = parseFloat(memStr) || 0;
    if (!name || !pid) continue;
    procs.push({
      name: name.trim().replace(/\.exe$/i, ''),
      fullName: name.trim(),
      pid,
      memoryMB: memMB,
      commandline: cmdline.trim(),
      category: categorize(name),
    });
  }
  procs.sort((a, b) => (a.name.toLowerCase() === b.name.toLowerCase() ? a.pid.localeCompare(b.pid) : a.name.toLowerCase().localeCompare(b.name.toLowerCase())));
  return procs;
}

function killProcess(pid, killTree) {
  return new Promise((resolve) => {
    const args = ['/F'];
    if (killTree) args.push('/T');
    args.push('/PID', String(pid));
    execFile('taskkill.exe', args, { windowsHide: true }, (err, stdout, stderr) => {
      resolve({ pid, ok: !err, output: (stdout || stderr || '').trim() });
    });
  });
}

async function readSaved(pluginRoot) {
  try {
    const raw = await readFile(join(pluginRoot, SAVED_FILE), 'utf8');
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

async function writeSaved(pluginRoot, list) {
  await writeFile(join(pluginRoot, SAVED_FILE), JSON.stringify(list, null, 2), 'utf8');
}

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', (chunk) => { data += chunk; });
    req.on('end', () => {
      if (!data) return resolve({});
      try { resolve(JSON.parse(data)); } catch (e) { reject(e); }
    });
    req.on('error', reject);
  });
}

function sendJson(res, status, payload) {
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
  res.end(JSON.stringify(payload));
}

export async function start(context) {
  const clientEntry = await readFile(join(context.pluginRoot, 'miniapp/client/index.html'));
  const apiBase = '/api';

  const server = createServer((request, response) => {
    handleRequest(request, response, { clientEntry, apiBase, context }).catch((err) => {
      try {
        sendJson(response, 500, { error: 'server_error', message: String(err.message || err) });
      } catch { /* socket may be closed */ }
    });
  });

  await new Promise((resolve, reject) => {
    const onError = (error) => reject(error);
    server.once('error', onError);
    server.listen(context.listen.port, context.listen.host, () => {
      server.off('error', onError);
      resolve();
    });
  });

  let disposal;
  const dispose = () => {
    if (disposal) return disposal;
    context.signal.removeEventListener('abort', onAbort);
    disposal = new Promise((resolve, reject) => {
      server.close((error) => (error ? reject(error) : resolve()));
    });
    return disposal;
  };
  const onAbort = () => {
    void dispose().catch(() => undefined);
  };
  context.signal.addEventListener('abort', onAbort, { once: true });
  if (context.signal.aborted) await dispose();

  return { dispose };
}

async function handleRequest(request, response, { clientEntry, apiBase, context }) {
  const url = new URL(request.url ?? '/', 'http://miniapp.local');
  const path = url.pathname;
  const method = request.method;

  if (method === 'GET' && path === '/dashboard') {
    response.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    response.end(clientEntry);
    return;
  }

  if (method === 'GET' && path === `${apiBase}/processes`) {
    const procs = await listProcesses();
    sendJson(response, 200, { processes: procs, timestamp: Date.now() });
    return;
  }

  if (method === 'POST' && path === `${apiBase}/kill`) {
    const body = await parseBody(request);
    const pids = Array.isArray(body.pids) ? body.pids.map(String) : [];
    const killTree = body.killTree !== false;
    const results = await Promise.all(pids.map((p) => killProcess(p, killTree)));
    sendJson(response, 200, { results });
    return;
  }

  if (method === 'POST' && path === `${apiBase}/relaunch`) {
    const saved = await readSaved(context.pluginRoot);
    const launched = [];
    const failed = [];
    for (const proc of saved) {
      const cmd = proc.commandline;
      if (!cmd) { failed.push({ name: proc.name, reason: 'no_commandline' }); continue; }
      try {
        const child = spawn(cmd, [], { shell: true, detached: true, stdio: 'ignore', windowsHide: true });
        child.unref();
        launched.push({ name: proc.name, pid: proc.pid });
      } catch (e) {
        failed.push({ name: proc.name, reason: String(e.message || e) });
      }
    }
    sendJson(response, 200, { launched, failed });
    return;
  }

  if (method === 'GET' && path === `${apiBase}/saved`) {
    const saved = await readSaved(context.pluginRoot);
    sendJson(response, 200, { saved });
    return;
  }

  if (method === 'POST' && path === `${apiBase}/saved`) {
    const body = await parseBody(request);
    const items = Array.isArray(body.items) ? body.items : [];
    const current = await readSaved(context.pluginRoot);
    const keys = new Set(current.map((c) => `${c.name}|${c.pid}`));
    let added = 0;
    for (const it of items) {
      if (!it.commandline) continue;
      const key = `${it.name}|${it.pid}`;
      if (keys.has(key)) continue;
      current.push(it);
      keys.add(key);
      added++;
    }
    await writeSaved(context.pluginRoot, current);
    sendJson(response, 200, { added, total: current.length });
    return;
  }

  if (method === 'DELETE' && path === `${apiBase}/saved`) {
    await writeSaved(context.pluginRoot, []);
    sendJson(response, 200, { cleared: true });
    return;
  }

  sendJson(response, 404, { error: 'not_found', path });
}
