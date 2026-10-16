/* Runtime loading only. Gameplay, input, and rendering live in Python. */
(async () => {
  const status = document.getElementById('status');
  try {
    const py = await loadPyodide();
    status.textContent = 'Preparing supplies…';
    await py.loadPackage('micropip');
    await py.runPythonAsync('import micropip\nawait micropip.install("zapros==0.19.0")');
    for (const name of ['core.py', 'game.py']) {
      const response = await fetch(name);
      if (!response.ok) throw new Error(`Cannot load ${name}: ${response.status}`);
      py.FS.writeFile(name, await response.text());
    }
    status.textContent = 'Opening the lower hall…';
    await py.runPythonAsync('import game\nawait game.start()');
    window.dungeonPython = py;
  } catch (error) {
    console.error(error);
    status.textContent = 'The keep could not load. Check your internet connection, then reload. ' + error.message;
    document.getElementById('enter').textContent = 'Unable to enter';
  }
})();
