# export_pdf.ps1 — save a .pptx as PDF, for members to open on a phone.
#
# PDFs, not .pptx, are what go on the site: a member wants to look at it, not
# edit it, and a PDF opens on any phone without PowerPoint. Presenters get the
# editable deck by email instead.
#
#   pwsh export_pdf.ps1 -Pptx deck.pptx -Out deck.pdf

param(
    [Parameter(Mandatory = $true)][string]$Pptx,
    [Parameter(Mandatory = $true)][string]$Out
)

$ErrorActionPreference = "Stop"
$Pptx = (Resolve-Path $Pptx).Path
$dir = Split-Path -Parent $Out
if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
$Out = [System.IO.Path]::GetFullPath($Out)

$app = $null
$deck = $null
try {
    $app = New-Object -ComObject PowerPoint.Application
    $deck = $app.Presentations.Open($Pptx, $true, $false, $false)   # readonly, no window
    $deck.SaveAs($Out, 32)                                          # 32 = ppSaveAsPDF
    Write-Output "-> $Out"
}
finally {
    if ($deck) { try { $deck.Close() } catch {} }
    if ($app) { try { $app.Quit() } catch {} }
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null 2>$null
    [GC]::Collect()
}
