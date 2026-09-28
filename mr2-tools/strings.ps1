param(
  [Parameter(Mandatory=$true)][string]$Path,
  [Parameter(Mandatory=$true)][string]$Patterns,   # semicolon-separated
  [int]$Ctx = 150,
  [int]$Max = 12
)
$ErrorActionPreference = 'Stop'
$b = [System.IO.File]::ReadAllBytes($Path)
$s = [System.Text.Encoding]::ASCII.GetString($b)
$leaf = Split-Path $Path -Leaf
foreach ($pat in ($Patterns -split ';')) {
  if ([string]::IsNullOrWhiteSpace($pat)) { continue }
  "===== [$pat] in $leaf ====="
  $idx = 0; $n = 0
  while (($i = $s.IndexOf($pat, $idx, [System.StringComparison]::Ordinal)) -ge 0 -and $n -lt $Max) {
    $start = [Math]::Max(0, $i - $Ctx)
    $len   = [Math]::Min(($Ctx * 2) + $pat.Length, $s.Length - $start)
    $frag  = $s.Substring($start, $len) -replace '[^\x20-\x7e]', '.'
    "  @$i : $frag"
    $idx = $i + 1
    $n++
  }
  if ($n -eq 0) { "  (not found)" }
  ""
}
