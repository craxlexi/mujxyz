# Run from the existing muj-pulse project folder. Keeps ignored local secrets and data.
$ErrorActionPreference = 'Stop'
if (-not (Test-Path 'backend/app/main.py') -or -not (Test-Path 'frontend/package.json')) {
    throw 'Open PowerShell in the existing muj-pulse project folder first.'
}
$branch = 'work'
$tree = Invoke-RestMethod "https://api.github.com/repos/craxlexi/mujxyz/git/trees/$branch`?recursive=1"
if ($tree.truncated) { throw 'The source listing was incomplete; no files were changed.' }
$files = @($tree.tree | Where-Object { $_.type -eq 'blob' } | ForEach-Object { $_.path })
if ($files.Count -lt 10) { throw 'The source listing was incomplete; no files were changed.' }
$stage = Join-Path ([System.IO.Path]::GetTempPath()) ('muj-pulse-update-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stage | Out-Null
try {
    foreach ($file in $files) {
        $target = Join-Path $stage $file
        New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
        $url = 'https://raw.githubusercontent.com/craxlexi/mujxyz/' + $branch + '/' + $file
        Invoke-WebRequest -Uri $url -OutFile $target
    }
    foreach ($file in $files) {
        $target = Join-Path (Get-Location).Path $file
        New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
        Copy-Item -LiteralPath (Join-Path $stage $file) -Destination $target -Force
    }
    Write-Host "Updated $($files.Count) project files in place. Local .env, database, and dependencies were preserved."
} finally {
    Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
}
