# Convenience launcher for local review; makes no installation or network requests.
param(
    [ValidateSet('guided', 'discovery')]
    [string]$Mode = 'guided',
    [string]$SessionFile
)
$ErrorActionPreference = 'Stop'
$plannerScript = Join-Path $PSScriptRoot 'skills/ganbaru/scripts/ganbaru.py'
$plannerPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
$plannerArguments = @()
if (-not (Test-Path -LiteralPath $plannerPython)) {
    $plannerLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($plannerLauncher) {
        $plannerPython = $plannerLauncher.Source
        $plannerArguments = @('-3')
    } else {
        $plannerLauncher = Get-Command python -ErrorAction SilentlyContinue
        if ($plannerLauncher) {
            $plannerPython = $plannerLauncher.Source
        } else {
            $plannerPython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
            if (-not (Test-Path -LiteralPath $plannerPython)) {
                throw 'Install Python 3.10+ or create a .venv. No runtime packages are required. See README.md.'
            }
        }
    }
}
if ($SessionFile) {
    & $plannerPython @plannerArguments $plannerScript resume --file $SessionFile
} elseif ($PSBoundParameters.ContainsKey('Mode')) {
    & $plannerPython @plannerArguments $plannerScript start --mode $Mode
} else {
    # No mode given: Ganbaru offers any saved plans first, then asks how to start.
    & $plannerPython @plannerArguments $plannerScript start
}
exit $LASTEXITCODE
