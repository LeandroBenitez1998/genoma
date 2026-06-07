#!/usr/bin/env node

'use strict';

const { spawn, execFileSync } = require('child_process');
const path = require('path');
const os = require('os');

// ─── Constants ───────────────────────────────────────────────────────────────

const DEFAULT_BACKEND_PORT = 8000;
const FRONTEND_PORT = 3000;
const DEFAULT_HOST = '127.0.0.1';
const MIN_PYTHON_MAJOR = 3;
const MIN_PYTHON_MINOR = 10;

const isWindows = os.platform() === 'win32';
const python3 = isWindows ? 'python' : 'python3';
const pnpm = isWindows ? 'pnpm.cmd' : 'pnpm';

// ─── Arg parsing ─────────────────────────────────────────────────────────────

function parseArgs(argv) {
  const args = argv.slice(2);
  const subcommand = args[0] && !args[0].startsWith('--') ? args[0] : 'serve';
  const flags = {};
  let i = subcommand === 'serve' ? 0 : 1;

  flags.host = DEFAULT_HOST;
  flags.backendPort = DEFAULT_BACKEND_PORT;
  flags.frontendPort = FRONTEND_PORT;
  flags.dev = true;

  while (i < args.length) {
    switch (args[i]) {
      case '--host':
        flags.host = args[++i];
        break;
      case '--backend-port':
      case '--port':
        flags.backendPort = parseInt(args[++i], 10);
        if (isNaN(flags.backendPort) || flags.backendPort < 1 || flags.backendPort > 65535) {
          fatal(`Invalid port value`);
        }
        break;
      case '--frontend-port':
        flags.frontendPort = parseInt(args[++i], 10);
        if (isNaN(flags.frontendPort) || flags.frontendPort < 1 || flags.frontendPort > 65535) {
          fatal(`Invalid frontend port value`);
        }
        break;
      case '--dev':
        flags.dev = true;
        break;
      case '--prod':
        flags.dev = false;
        break;
      case '--help':
      case '-h':
        printHelp();
        process.exit(0);
        break;
      default:
        if (i > 0) fatal(`Unknown option: ${args[i]}`);
    }
    i++;
  }

  return { subcommand, ...flags };
}

function printHelp() {
  console.log(`
genoma - Agent-agnostic evolution dashboard

USAGE:
  genoma [command] [options]

COMMANDS:
  serve          Start backend + frontend (default)
  dev            Start backend + frontend in dev mode
  doctor         Check dependencies and connectivity
  mcp            Start only the MCP stdio server

OPTIONS:
  --host <ip>              Backend bind address (default: ${DEFAULT_HOST})
  --backend-port <num>     Backend port (default: ${DEFAULT_BACKEND_PORT})
  --frontend-port <num>    Frontend port (default: ${FRONTEND_PORT})
  --dev                    Start frontend in dev mode
  --prod                   Start frontend in production mode
  --help, -h               Show this help

EXAMPLES:
  genoma                         # serve on 127.0.0.1:8000 + :3000
  genoma serve --prod            # production mode
  genoma doctor                  # verify everything works
  genoma mcp                     # start only the MCP server
`);
}

// ─── Dependency checks ───────────────────────────────────────────────────────

function checkNode() {
  const [major] = process.versions.node.split('.').map(Number);
  if (major < 16) {
    fatal(`Node.js 16+ required. Found: ${process.version}`);
  }
}

function checkPython() {
  try {
    const raw = execFileSync(python3, ['--version'], {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
    }).trim();
    const match = raw.match(/Python\s+(\d+)\.(\d+)/i);
    if (!match) fatal(`Could not parse Python version from: "${raw}"`);
    const major = parseInt(match[1], 10);
    const minor = parseInt(match[2], 10);
    if (major < MIN_PYTHON_MAJOR || (major === MIN_PYTHON_MAJOR && minor < MIN_PYTHON_MINOR)) {
      fatal(`Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ required. Found: ${major}.${minor}`);
    }
  } catch (err) {
    fatal(`Python 3 not found. Install Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+.\n  Detail: ${err.message}`);
  }
}

function checkPnpm() {
  try {
    execFileSync(pnpm, ['--version'], {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
    });
  } catch {
    fatal('pnpm not found. Install it with: npm install -g pnpm');
  }
}

function checkDependencies() {
  checkNode();
  checkPython();
  checkPnpm();
  console.log('[genoma] All dependencies satisfied.');
}

// ─── Process management ──────────────────────────────────────────────────────

const children = new Map();

function spawnProcess(name, cmd, args, opts = {}) {
  const child = spawn(cmd, args, {
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env },
    ...opts,
  });
  children.set(name, child);

  child.stdout.on('data', (data) => {
    process.stdout.write(`[${name}] ${data}`);
  });
  child.stderr.on('data', (data) => {
    process.stderr.write(`[${name}] ${data}`);
  });
  child.on('error', (err) => {
    console.error(`[${name}] Failed to start: ${err.message}`);
    shutdown(1);
  });
  child.on('exit', (code, signal) => {
    if (!shuttingDown) {
      console.error(`[${name}] Exited unexpectedly (code=${code ?? 'null'}, signal=${signal ?? 'none'})`);
      shutdown(1);
    }
  });
  return child;
}

let shuttingDown = false;

function shutdown(exitCode = 0) {
  if (shuttingDown) return;
  shuttingDown = true;
  console.log('\n[genoma] Shutting down...');
  for (const [name, child] of children.entries()) {
    if (!child.killed) {
      console.log(`[genoma] Stopping ${name} (pid ${child.pid})...`);
      child.kill('SIGTERM');
    }
  }
  setTimeout(() => {
    for (const child of children.values()) {
      if (!child.killed) child.kill('SIGKILL');
    }
    process.exit(exitCode);
  }, 3000);
}

// ─── Startup ─────────────────────────────────────────────────────────────────

function startBackend(host, port) {
  return spawnProcess('backend', python3, [
    '-m', 'uvicorn', 'backend.main:app',
    '--host', host,
    '--port', String(port),
  ]);
}

function startMcp() {
  return spawnProcess('mcp', python3, ['-m', 'backend.mcp_server']);
}

function startFrontend(dev) {
  const script = dev ? 'dev' : 'start';
  return spawnProcess('frontend', pnpm, [script]);
}

function printBanner(host, backendPort, frontendPort, dev) {
  console.log(`
  ╔══════════════════════════════════════╗
  ║           genoma stack               ║
  ╠══════════════════════════════════════╣
  ║  Backend  → http://${host}:${String(backendPort).padEnd(5)}  ║
  ║  Frontend → http://localhost:${String(frontendPort).padEnd(5)}  ║
  ║  MCP      → stdio ready              ║
  ╚══════════════════════════════════════╝
  Mode: ${dev ? 'development' : 'production'}
  Press Ctrl+C to stop all processes.
`);
}

// ─── Doctor ──────────────────────────────────────────────────────────────────

function runDoctor() {
  console.log('[genoma] Running doctor...\n');

  // Node
  try {
    checkNode();
    console.log(`  ✓ Node.js ${process.version}`);
  } catch (e) {
    console.log(`  ✗ ${e.message}`);
  }

  // Python
  try {
    checkPython();
    const raw = execFileSync(python3, ['--version'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
    console.log(`  ✓ ${raw}`);
  } catch (e) {
    console.log(`  ✗ ${e.message}`);
  }

  // pnpm
  try {
    checkPnpm();
    const raw = execFileSync(pnpm, ['--version'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
    console.log(`  ✓ pnpm ${raw}`);
  } catch (e) {
    console.log(`  ✗ ${e.message}`);
  }

  // Python deps
  for (const mod of ['fastapi', 'uvicorn', 'dotenv', 'pydantic']) {
    try {
      execFileSync(python3, ['-c', `import ${mod}; print('ok')`], { encoding: 'utf8', stdio: 'pipe' });
      console.log(`  ✓ python module: ${mod}`);
    } catch {
      console.log(`  ✗ python module: ${mod} (run: pip install -r backend/requirements.txt)`);
    }
  }

  // Backend connectivity (if it's running)
  const http = require('http');
  const req = http.get(`http://127.0.0.1:${DEFAULT_BACKEND_PORT}/api/health`, (res) => {
    let body = '';
    res.on('data', (c) => (body += c));
    res.on('end', () => {
      try {
        const data = JSON.parse(body);
        console.log(`  ✓ Backend health: ${data.status} (${data.skills_count} skills)`);
      } catch {
        console.log(`  ∼ Backend responded (non-JSON)`);
      }
      process.exit(0);
    });
  });
  req.on('error', () => {
    console.log(`  ∼ Backend not reachable on :${DEFAULT_BACKEND_PORT} (start with: genoma serve)`);
    process.exit(0);
  });
  req.setTimeout(3000, () => { req.destroy(); console.log('  ∼ Backend timed out'); process.exit(0); });
}

// ─── Signal handlers ─────────────────────────────────────────────────────────

process.on('SIGINT', () => shutdown(0));
process.on('SIGTERM', () => shutdown(0));
if (!isWindows) process.on('SIGHUP', () => shutdown(0));

// ─── Helpers ─────────────────────────────────────────────────────────────────

function fatal(message) {
  console.error(`[genoma] ERROR: ${message}`);
  process.exit(1);
}

// ─── Main ─────────────────────────────────────────────────────────────────────

function main() {
  const { subcommand, host, backendPort, frontendPort, dev } = parseArgs(process.argv);

  switch (subcommand) {
    case 'doctor':
      console.log('[genoma] Checking dependencies...');
      checkDependencies();
      runDoctor();
      return;

    case 'mcp':
      console.log('[genoma] Starting MCP server (stdio)...');
      startMcp();
      return;

    case 'serve':
    case 'dev':
      console.log('[genoma] Checking dependencies...');
      checkDependencies();
      printBanner(host, backendPort, frontendPort, dev);
      startBackend(host, backendPort);
      startFrontend(dev);
      return;

    default:
      fatal(`Unknown command: ${subcommand}\nRun: genoma --help`);
  }
}

main();
