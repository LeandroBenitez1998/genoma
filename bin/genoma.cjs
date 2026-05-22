#!/usr/bin/env node

'use strict';

const { spawn, execFileSync } = require('child_process');
const path = require('path');
const os = require('os');

// ─── Constants ───────────────────────────────────────────────────────────────

const DEFAULT_PORT = 8000;
const FRONTEND_PORT = 3000;
const MIN_PYTHON_MAJOR = 3;
const MIN_PYTHON_MINOR = 10;

const isWindows = os.platform() === 'win32';
const python3 = isWindows ? 'python' : 'python3';
const pnpm = isWindows ? 'pnpm.cmd' : 'pnpm';

// ─── Arg parsing ─────────────────────────────────────────────────────────────

function parseArgs(argv) {
  const args = argv.slice(2);
  let port = DEFAULT_PORT;
  let dev = true;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--port') {
      const value = parseInt(args[i + 1], 10);
      if (!isNaN(value) && value > 0 && value < 65536) {
        port = value;
        i++;
      } else {
        fatal(`Invalid --port value: "${args[i + 1]}"`);
      }
    } else if (args[i] === '--dev') {
      dev = true;
    } else if (args[i] === '--help' || args[i] === '-h') {
      printHelp();
      process.exit(0);
    }
  }

  return { port, dev };
}

function printHelp() {
  console.log(`
Usage: genoma [options]

Options:
  --port <number>   Backend port (default: ${DEFAULT_PORT})
  --dev             Run frontend in development mode (default: false)
  --help, -h        Show this help message
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

    // "Python 3.11.2"
    const match = raw.match(/Python\s+(\d+)\.(\d+)/i);
    if (!match) {
      fatal(`Could not parse Python version from: "${raw}"`);
    }

    const major = parseInt(match[1], 10);
    const minor = parseInt(match[2], 10);

    if (
      major < MIN_PYTHON_MAJOR ||
      (major === MIN_PYTHON_MAJOR && minor < MIN_PYTHON_MINOR)
    ) {
      fatal(
        `Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ required. ` +
          `Found: ${major}.${minor}`
      );
    }
  } catch (err) {
    fatal(
      `Python 3 not found. Install Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ and ensure it is in your PATH.\n` +
        `  Detail: ${err.message}`
    );
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
}

// ─── Process management ──────────────────────────────────────────────────────

const children = new Map(); // name → ChildProcess

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
      console.error(
        `[${name}] Exited unexpectedly (code=${code ?? 'null'}, signal=${signal ?? 'none'})`
      );
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

  // Give processes a moment to clean up, then hard-kill stragglers
  setTimeout(() => {
    for (const child of children.values()) {
      if (!child.killed) child.kill('SIGKILL');
    }
    process.exit(exitCode);
  }, 3000);
}

// ─── Startup ─────────────────────────────────────────────────────────────────

function startBackend(port) {
  return spawnProcess('backend', python3, [
    '-m',
    'uvicorn',
    'backend.main:app',
    '--host',
    '0.0.0.0',
    '--port',
    String(port),
  ]);
}

function startMcp() {
  return spawnProcess('mcp', python3, ['-m', 'backend.mcp_server']);
}

function startFrontend(dev) {
  const script = dev ? 'dev' : 'start';
  return spawnProcess('frontend', pnpm, [script]);
}

function printBanner(port, dev) {
  console.log(`
  ╔══════════════════════════════════════╗
  ║           genoma stack               ║
  ╠══════════════════════════════════════╣
  ║  Backend  → http://localhost:${String(port).padEnd(5)}  ║
  ║  Frontend → http://localhost:${String(FRONTEND_PORT).padEnd(5)}  ║
  ║  MCP      → stdio ready              ║
  ╚══════════════════════════════════════╝

  Mode: ${dev ? 'development' : 'production'}
  Press Ctrl+C to stop all processes.
`);
}

// ─── Signal handlers ─────────────────────────────────────────────────────────

process.on('SIGINT', () => shutdown(0));
process.on('SIGTERM', () => shutdown(0));

// Windows does not support SIGHUP
if (!isWindows) {
  process.on('SIGHUP', () => shutdown(0));
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function fatal(message) {
  console.error(`[genoma] ERROR: ${message}`);
  process.exit(1);
}

// ─── Main ─────────────────────────────────────────────────────────────────────

function main() {
  const { port, dev } = parseArgs(process.argv);

  console.log('[genoma] Checking dependencies...');
  checkDependencies();
  console.log('[genoma] All dependencies satisfied.');

  printBanner(port, dev);

  startBackend(port);
  // MCP server runs as part of backend; separate process not needed with stdio:ignore
  // Agents interact via REST API endpoints (/api/runs, /api/evolution, etc.)
  // startMcp();
  startFrontend(dev);
}

main();
