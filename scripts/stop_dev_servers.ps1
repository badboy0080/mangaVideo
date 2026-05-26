$ErrorActionPreference = "SilentlyContinue"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Ports = @(8765, 5173, 5174, 5175)
$Stopped = @()

function Get-ParentDevPids {
  param([int[]] $SeedPids)

  $Out = New-Object System.Collections.Generic.List[int]
  foreach ($SeedPid in $SeedPids) {
    $Current = Get-CimInstance Win32_Process -Filter "ProcessId = $SeedPid"
    while ($Current) {
      if (-not $Out.Contains([int]$Current.ProcessId)) {
        $Out.Add([int]$Current.ProcessId)
      }

      $Parent = Get-CimInstance Win32_Process -Filter "ProcessId = $($Current.ParentProcessId)"
      if (-not $Parent) { break }

      $ParentCommand = [string]$Parent.CommandLine
      $ParentName = [string]$Parent.Name
      $IsDevParent =
        ($ParentName -in @("node.exe", "cmd.exe", "powershell.exe", "pwsh.exe")) -and
        (
          $ParentCommand -like "*npm*run*dev*" -or
          $ParentCommand -like "*vite*" -or
          $ParentCommand -like "*uvicorn*server.main*" -or
          $ParentCommand -like "*$ProjectRoot*"
        )

      if (-not $IsDevParent) { break }
      $Current = $Parent
    }
  }
  return $Out.ToArray()
}

$PortPids = @(
  Get-NetTCPConnection -LocalPort $Ports |
    Where-Object { $_.OwningProcess -gt 0 } |
    Select-Object -ExpandProperty OwningProcess -Unique
)

$ProcessPids = @(
  Get-CimInstance Win32_Process |
    Where-Object {
      ($_.CommandLine -like "*$ProjectRoot*") -and
      (
        $_.CommandLine -like "*uvicorn*server.main*" -or
        $_.CommandLine -like "*vite*" -or
        $_.CommandLine -like "*npm*run*dev*"
      )
    } |
    Select-Object -ExpandProperty ProcessId -Unique
)

$SeedPids = @($PortPids + $ProcessPids) | Where-Object { $_ } | Select-Object -Unique
$AllPids = @(Get-ParentDevPids -SeedPids $SeedPids) | Where-Object { $_ } | Select-Object -Unique

foreach ($ProcessId in $AllPids) {
  $Proc = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId"
  if (-not $Proc) { continue }

  $IsProjectProc =
    ($Proc.CommandLine -like "*$ProjectRoot*") -or
    ($Proc.CommandLine -like "*uvicorn*server.main*") -or
    ($Proc.CommandLine -like "*vite*") -or
    ($Proc.CommandLine -like "*npm*run*dev*")

  if ($IsProjectProc) {
    Stop-Process -Id $ProcessId -Force
    $Stopped += "$ProcessId $($Proc.Name)"
  }
}

if ($Stopped.Count -eq 0) {
  Write-Host "No manga-pipeline dev server processes were running."
} else {
  Write-Host "Stopped manga-pipeline dev server processes:"
  $Stopped | ForEach-Object { Write-Host "  $_" }
}
