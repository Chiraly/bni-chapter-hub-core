# render_preview.ps1 — export a .pptx to PNGs so the slides can actually be looked at.
# Visual QA is not optional: text overflow and collisions do not show up in python-pptx.
#
#   pwsh render_preview.ps1 -Pptx deck.pptx -OutDir preview [-Width 1600]

param(
    [Parameter(Mandatory = $true)][string]$Pptx,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [int]$Width = 1600
)

$ErrorActionPreference = "Stop"
$Pptx = (Resolve-Path $Pptx).Path
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }
$OutDir = (Resolve-Path $OutDir).Path
Get-ChildItem $OutDir -Filter *.png -ErrorAction SilentlyContinue | Remove-Item -Force

$app = $null
$deck = $null
try {
    $app = New-Object -ComObject PowerPoint.Application
    $deck = $app.Presentations.Open($Pptx, $true, $false, $false)  # readonly, no window
    $height = [int][Math]::Round($Width * $deck.PageSetup.SlideHeight / $deck.PageSetup.SlideWidth)
    $deck.Export($OutDir, "PNG", $Width, $height)
    $n = (Get-ChildItem $OutDir -Filter *.png).Count
    Write-Output "Exported $n slide(s) to $OutDir at ${Width}x${height}"
}
finally {
    if ($deck) { try { $deck.Close() } catch {} }
    if ($app) { try { $app.Quit() } catch {} }
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null 2>$null
    [GC]::Collect()
}
