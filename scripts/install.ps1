param(
    [Parameter(Mandatory = $true)][string]$Destination,
    [switch]$WhatIf
)
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path (Join-Path $PSScriptRoot '..\skills')).Path
$target = [System.IO.Path]::GetFullPath($Destination)
if ($target.TrimEnd('\') -eq $source.TrimEnd('\') -or $target.StartsWith($source.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Destination must not be inside the source skills tree'
}
$probe = $target
while ($probe) {
    if ((Test-Path -LiteralPath $probe) -and ((Get-Item -LiteralPath $probe -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Target reparse point rejected: $probe" }
    $next = Split-Path -Parent $probe
    if ($next -eq $probe) { break }
    $probe = $next
}
$skills = @(Get-ChildItem -LiteralPath $source -Recurse -File -Filter 'SKILL.md')
if ($skills.Count -eq 0) { throw 'No skills found' }
$plan = @()
foreach ($skill in $skills) {
    $skillSource = $skill.Directory.FullName
    $skillTarget = Join-Path $target $skill.Directory.Name
    $files = @(Get-ChildItem -LiteralPath $skillSource -Recurse -File)
    foreach ($file in $files) {
        if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Symlink/reparse point rejected: $($file.FullName)" }
        $relative = $file.FullName.Substring($skillSource.Length + 1)
        $existing = Join-Path $skillTarget $relative
        if (Test-Path -LiteralPath $existing) {
            if ((Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $existing -Algorithm SHA256).Hash) {
                throw "Existing local file differs: $existing"
            }
        } else {
            $plan += [pscustomobject]@{ Source = $file.FullName; Target = $existing }
        }
    }
}
if ($WhatIf) {
    "Would install $($plan.Count) files from $($skills.Count) skills into $target"
    exit 0
}
foreach ($item in $plan) {
    $parent = Split-Path -Parent $item.Target
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    Copy-Item -LiteralPath $item.Source -Destination $item.Target
}
"Installed $($plan.Count) files from $($skills.Count) skills into $target"
