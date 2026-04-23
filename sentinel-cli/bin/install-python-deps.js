const { spawnSync } = require('child_process');
const path = require('path');
const os = require('os');
const fs = require('fs');

console.log('[Sentinel] Installing Python dependencies...');

const sentinelHome = path.join(os.homedir(), '.sentinel');
if (!fs.existsSync(sentinelHome)) {
  fs.mkdirSync(sentinelHome, { recursive: true });
}

const venvPath = path.join(sentinelHome, 'venv');
const isWin = os.platform() === 'win32';
const pythonCmd = isWin ? 'python' : 'python3';

// Create virtual environment
if (!fs.existsSync(venvPath)) {
  console.log(`[Sentinel] Creating virtual environment at ${venvPath}...`);
  spawnSync(pythonCmd, ['-m', 'venv', venvPath], { stdio: 'inherit' });
}

const pipBin = isWin ? path.join(venvPath, 'Scripts', 'pip.exe') : path.join(venvPath, 'bin', 'pip');

if (!fs.existsSync(pipBin)) {
  console.error('[Sentinel] Error: Failed to create Python virtual environment.');
  process.exit(1);
}

// Install dependencies from requirements.txt and pyproject.toml
const projectDir = path.join(__dirname, '..');
console.log(`[Sentinel] Running: ${pipBin} install -e ${projectDir}`);

const result = spawnSync(pipBin, ['install', '-e', projectDir], {
  stdio: 'inherit',
  cwd: projectDir
});

if (result.status === 0) {
  console.log('[Sentinel] Python dependencies installed successfully.');
} else {
  console.error('[Sentinel] Error installing Python dependencies.');
  process.exit(result.status || 1);
}
