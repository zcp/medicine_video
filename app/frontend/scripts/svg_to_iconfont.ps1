param(
    [string]$InputDir = "src/static/icon_svg",
    [string]$OutputDir = "src/static/icon_svg_clean",
    [switch]$UseInkscape,
    [string]$InkscapePath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-AbsolutePath {
    param([string]$PathText)

    if ([System.IO.Path]::IsPathRooted($PathText)) {
        return (Resolve-Path -Path $PathText).Path
    }

    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $PathText))
}

function Normalize-SvgText {
    param([string]$Text)

    $t = $Text

    # Remove XML/DOCTYPE/comments.
    $t = [regex]::Replace($t, '<\?xml[^>]*\?>', '', 'IgnoreCase')
    $t = [regex]::Replace($t, '<!DOCTYPE[^>]*>', '', 'IgnoreCase')
    $t = [regex]::Replace($t, '<!--[\s\S]*?-->', '', 'IgnoreCase')

    # Remove custom non-standard attributes often exported by icon tools.
    $t = [regex]::Replace($t, '\sdata-follow-(stroke|fill)="[^"]*"', '', 'IgnoreCase')

    # Remove defs/mask/clipPath/style/script blocks.
    $t = [regex]::Replace($t, '<defs[\s\S]*?</defs>', '', 'IgnoreCase')
    $t = [regex]::Replace($t, '<clipPath[\s\S]*?</clipPath>', '', 'IgnoreCase')
    $t = [regex]::Replace($t, '<mask[\s\S]*?</mask>', '', 'IgnoreCase')
    $t = [regex]::Replace($t, '<style[\s\S]*?</style>', '', 'IgnoreCase')
    $t = [regex]::Replace($t, '<script[\s\S]*?</script>', '', 'IgnoreCase')

    # Remove clip/mask/filter attributes that depend on removed defs.
    $t = [regex]::Replace($t, '\sclip-path="[^"]*"', '', 'IgnoreCase')
    $t = [regex]::Replace($t, '\smask="[^"]*"', '', 'IgnoreCase')
    $t = [regex]::Replace($t, '\sfilter="[^"]*"', '', 'IgnoreCase')

    # Normalize root svg size props to viewBox-driven scaling.
    $t = [regex]::Replace($t, '(<svg\b[^>]*?)\swidth="[^"]*"', '$1', 'IgnoreCase')
    $t = [regex]::Replace($t, '(<svg\b[^>]*?)\sheight="[^"]*"', '$1', 'IgnoreCase')

    # Ensure xmlns exists on root svg.
    if ($t -match '<svg\b' -and $t -notmatch 'xmlns="http://www\.w3\.org/2000/svg"') {
        $t = [regex]::Replace(
            $t,
            '<svg\b',
            '<svg xmlns="http://www.w3.org/2000/svg"',
            'IgnoreCase'
        )
    }

    # Trim and compact line breaks.
    $t = $t.Trim()
    $t = [regex]::Replace($t, '>\s+<', '><')

    return $t + "`n"
}

function Get-InkscapeExecutable {
    param([string]$CustomPath)

    if (-not [string]::IsNullOrWhiteSpace($CustomPath)) {
        if (Test-Path -Path $CustomPath) {
            return (Resolve-Path -Path $CustomPath).Path
        }

        throw "InkscapePath does not exist: $CustomPath"
    }

    $cmd = Get-Command inkscape -ErrorAction SilentlyContinue
    if ($null -ne $cmd) {
        return $cmd.Source
    }

    $possible = @(
        "C:\Program Files\Inkscape\bin\inkscape.exe",
        "C:\Program Files\Inkscape\inkscape.exe"
    )

    foreach ($p in $possible) {
        if (Test-Path -Path $p) {
            return $p
        }
    }

    return ""
}

$inputAbs = Resolve-AbsolutePath -PathText $InputDir
if (-not (Test-Path -Path $inputAbs)) {
    throw "Input directory not found: $inputAbs"
}

$outputAbs = [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $OutputDir))
New-Item -ItemType Directory -Force -Path $outputAbs | Out-Null

$svgFiles = Get-ChildItem -Path $inputAbs -Filter *.svg -File | Sort-Object Name
if ($svgFiles.Count -eq 0) {
    throw "No .svg files found in $inputAbs"
}

$inkscapeExe = ""
if ($UseInkscape) {
    $inkscapeExe = Get-InkscapeExecutable -CustomPath $InkscapePath
    if ([string]::IsNullOrWhiteSpace($inkscapeExe)) {
        throw "UseInkscape specified but Inkscape was not found. Install Inkscape or pass -InkscapePath."
    }
}

$report = @()

foreach ($file in $svgFiles) {
    $raw = Get-Content -Path $file.FullName -Raw -Encoding UTF8
    $normalized = Normalize-SvgText -Text $raw

    $outFile = Join-Path $outputAbs $file.Name
    Set-Content -Path $outFile -Value $normalized -Encoding UTF8

    if ($UseInkscape) {
        $actions = "select-all;object-stroke-to-path;vacuum-defs;export-filename:$outFile;export-plain-svg;export-do;file-close"
        & $inkscapeExe $outFile "--actions=$actions" | Out-Null
    }

    $content = Get-Content -Path $outFile -Raw -Encoding UTF8

    $item = [PSCustomObject]@{
        FileName = $file.Name
        HasStroke = [bool]($content -match '\bstroke\s*=')
        HasDefs = [bool]($content -match '<defs\b')
        HasClipPath = [bool]($content -match '<clipPath\b|\bclip-path\s*=')
        HasMask = [bool]($content -match '<mask\b|\bmask\s*=')
        HasScript = [bool]($content -match '<script\b')
    }

    $report += $item
}

$reportPath = Join-Path $outputAbs "iconfont-upload-check.csv"
$report | Export-Csv -Path $reportPath -NoTypeInformation -Encoding UTF8

$needManual = $report | Where-Object { $_.HasStroke -or $_.HasDefs -or $_.HasClipPath -or $_.HasMask -or $_.HasScript }

Write-Host "Processed $($svgFiles.Count) SVG files."
Write-Host "Output directory: $outputAbs"
Write-Host "Report: $reportPath"

if ($needManual.Count -gt 0) {
    Write-Warning "Some files still contain stroke/defs/clip/mask/script and may fail in iconfont.cn. Review iconfont-upload-check.csv."
} else {
    Write-Host "All files passed the basic structural checks."
}
