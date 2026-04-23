#!/usr/bin/env node

const { spawnSync } = require('child_process');
const path = require('path');
const os = require('os');
const fs = require('fs');

// We install python dependencies into a virtual environment
// in ~/.sentinel/venv during the npm postinstall phase.
const sentinelHome = path.join(os.homedir(), '.sentinel');
const venvPath = path.join(sentinelHome, 'venv');
const isWin = os.platform() === 'win32';
const pythonBin = isWin ? path.join(venvPath, 'Scripts', 'python.exe') : path.join(venvPath, 'bin', 'python');

// If the virtual environment doesn't exist, we run a fallback attempt
if (!fs.existsSync(pythonBin)) {
  console.error('\n[Sentinel] Error: Python virtual environment not found.');
  console.error('[Sentinel] Please try running npm install -g sentinel-security again.\n');
  process.exit(1);
}

// Find main.py
const mainPy = path.join(__dirname, '..', 'src', 'main.py');

// Pass all arguments down to the python CLI
const args = process.argv.slice(2);
const result = spawnSync(pythonBin, [mainPy, ...args], {
  stdio: 'inherit',
  env: { ...process.env, PYTHONPATH: path.join(__dirname, '..') }
});

process.exit(result.status || 0);
