#!/usr/bin/env node
"use strict";
// A thin launcher. agent-dish is a Python program (standard library only); this finds Python 3.9+, points it at the
// copy bundled in this package, and hands over the terminal. No dependencies, no install scripts, no network access.
const { spawn, spawnSync } = require("node:child_process");
const path = require("node:path");

const bundled = path.join(__dirname, "..", "python");
const candidates =
  process.platform === "win32"
    ? [
        ["py", ["-3"]],
        ["python", []],
        ["python3", []],
      ]
    : [
        ["python3", []],
        ["python", []],
      ];

function usable([cmd, pre]) {
  const probe = spawnSync(cmd, [...pre, "-c", "import sys; print(sys.version_info[0], sys.version_info[1])"], {
    encoding: "utf8",
  });
  if (probe.status !== 0) return false;
  const [major, minor] = probe.stdout.trim().split(" ").map(Number);
  return major === 3 && minor >= 9;
}

const python = candidates.find(usable);
if (!python) {
  console.error(
    "agent-dish needs Python 3.9 or newer on your PATH (it is a Python program, packaged for npm).\n" +
      "Install Python from https://www.python.org/downloads/ and try again.",
  );
  process.exit(1);
}

const [cmd, pre] = python;
const child = spawn(cmd, [...pre, "-m", "agent_dish.cli", ...process.argv.slice(2)], {
  stdio: "inherit",
  env: {
    ...process.env,
    PYTHONPATH: [bundled, process.env.PYTHONPATH].filter(Boolean).join(path.delimiter),
    PYTHONDONTWRITEBYTECODE: "1", // do not write into a global node_modules
  },
});
for (const signal of ["SIGINT", "SIGTERM"]) process.on(signal, () => child.kill(signal));
child.on("error", (err) => {
  console.error(`agent-dish could not start Python: ${err.message}`);
  process.exit(1);
});
child.on("exit", (code, signal) => process.exit(code ?? (signal ? 1 : 0)));
