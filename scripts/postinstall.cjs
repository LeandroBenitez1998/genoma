#!/usr/bin/env node

'use strict';

const { execSync } = require('child_process');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '..');
const REQUIREMENTS_FILE = path.join(ROOT_DIR, 'backend', 'requirements.txt');

function getPythonVersion() {
  try {
    const output = execSync('python3 --version', { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
    const match = output.match(/Python (\d+)\.(\d+)/);
    if (!match) return null;
    return { major: parseInt(match[1], 10), minor: parseInt(match[2], 10) };
  } catch {
    return null;
  }
}

function main() {
  const version = getPythonVersion();

  if (!version) {
    console.warn('Warning: Python not found, skipping backend deps');
    return;
  }

  if (version.major < 3 || (version.major === 3 && version.minor < 10)) {
    console.warn(
      `Warning: Python 3.10+ required (found ${version.major}.${version.minor}), skipping backend deps`
    );
    return;
  }

  console.log('Installing Python dependencies...');

  try {
    execSync(`pip install -r "${REQUIREMENTS_FILE}"`, {
      cwd: ROOT_DIR,
      stdio: 'inherit',
    });
    console.log('Python dependencies installed');
  } catch (err) {
    console.warn(`Warning: Failed to install Python dependencies — ${err.message}`);
  }
}

main();
