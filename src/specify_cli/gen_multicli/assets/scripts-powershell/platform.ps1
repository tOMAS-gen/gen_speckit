#Requires -Version 5.1
<#
.SYNOPSIS
  Helpers de plataforma del sistema multi-CLI. UNICO lugar del proyecto donde se
  permite logica sensible al sistema operativo (FR-014 de la feature 003).
.DESCRIPTION
  Compatible con Windows PowerShell 5.1 y PowerShell 7+ (windows/linux/macos).
  Todos los demas scripts consumen estas primitivas: ningun otro archivo puede
  mencionar cmd.exe, taskkill, NUL ni separadores de ruta fijos.
.NOTES
  Solo funciones (sin punto de entrada): pensado para dot-source.
#>

Set-StrictMode -Version 2.0

function Get-OsFamily {
    # 'windows' | 'linux' | 'macos'. En 5.1 las variables $IsWindows/$IsLinux no
    # existen: Windows PowerShell solo corre en Windows.
    if ($PSVersionTable.PSVersion.Major -lt 6) { return 'windows' }
    if ($IsWindows) { return 'windows' }
    if ($IsMacOS)   { return 'macos' }
    'linux'
}

function Get-NullDevice {
    if ((Get-OsFamily) -eq 'windows') { 'NUL' } else { '/dev/null' }
}

function Expand-PortablePath {
    # Expande ~, $HOME, %VARIABLES% y variables de entorno segun el SO actual.
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return $Path }
    $p = $Path
    if ($p.StartsWith('~')) { $p = $HOME + $p.Substring(1) }
    $p = $p -replace '\$HOME', $HOME
    $p = [System.Environment]::ExpandEnvironmentVariables($p)
    # Normalizar separadores al del SO actual.
    $sep = [System.IO.Path]::DirectorySeparatorChar
    $p -replace '[\\/]', $sep
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function Resolve-Executable {
    <#
      Resuelve la ruta completa de un ejecutable de forma portable.
      - ExeHints: rutas candidatas directas (del catalogo/inventario), expandidas con
        Expand-PortablePath; la primera existente gana.
      - En Windows prueba sufijos .exe/.cmd/.bat (los hijos de proceso no siempre
        heredan un PATH util); en Unix usa la resolucion normal de Get-Command.
      Devuelve la ruta completa o $null.
    #>
    param(
        [string]$Name,
        [string[]]$ExeHints = @()
    )
    foreach ($hint in $ExeHints) {
        $expanded = Expand-PortablePath $hint
        # Los hints pueden tener comodines (paquetes con version en la ruta).
        $found = Get-Item -Path $expanded -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -ne $found) { return $found.FullName }
        $globbed = Get-ChildItem -Path $expanded -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -ne $globbed) { return $globbed.FullName }
    }
    if ((Get-OsFamily) -eq 'windows') {
        foreach ($candidate in @("$Name.exe", "$Name.cmd", "$Name.bat", $Name)) {
            $info = Get-Command $candidate -ErrorAction SilentlyContinue |
                Where-Object { $_.Source -match '\.(exe|cmd|bat)$' } | Select-Object -First 1
            if ($null -ne $info) { return $info.Source }
        }
        return $null
    }
    $cmd = Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -ne $cmd) { return $cmd.Source }
    $null
}

function Stop-ProcessTree {
    # Mata el proceso Y sus hijos. En .NET Core (pwsh 7+) Kill($true) es nativo;
    # en Windows PowerShell 5.1 se usa taskkill /T.
    param([System.Diagnostics.Process]$Process)
    if ($null -eq $Process) { return }
    try {
        if ($PSVersionTable.PSVersion.Major -ge 6) {
            $Process.Kill($true)
        } else {
            & taskkill /T /F /PID $Process.Id 2>$null | Out-Null
        }
    } catch {
        try { $Process.Kill() } catch { }
    }
}

function Invoke-PortableProcess {
    <#
      Ejecuta una linea de comando con timeout y captura, via un wrapper-archivo que:
      - hereda el PATH de esta sesion (los hijos no siempre lo reciben util),
      - cierra stdin con el null device (algunos CLIs esperan EOF para arrancar),
      - queda en disco como evidencia auditable del comando exacto.
      Windows: wrapper .cmd ejecutado por cmd.exe. Linux/macOS: wrapper .sh por /bin/sh.
      Devuelve @{ exitCode; timedOut }.
    #>
    param(
        [string]$Command,
        [int]$TimeoutSeconds,
        [string]$OutFile,
        [string]$ErrFile,
        [string]$WorkDir = (Get-Location).Path
    )
    $os = Get-OsFamily
    if ($os -eq 'windows') {
        $wrapper = "$OutFile.cmd"
        $batchCommand = $Command -replace '%', '%%'
        $pathLine = 'set "PATH=' + ($env:PATH -replace '%', '%%') + '"'
        Set-Content -Path $wrapper -Value "@echo off`r`n$pathLine`r`n$batchCommand < NUL`r`nexit /b %ERRORLEVEL%" -Encoding Default
        $exe = 'cmd.exe'; $args = "/d /c `"$wrapper`""
    } else {
        $wrapper = "$OutFile.sh"
        # Comillas simples cerradas de forma segura para sh.
        $safePath = $env:PATH -replace "'", "'\''"
        $lines = @('#!/bin/sh', "export PATH='$safePath'", "$Command < /dev/null", 'exit $?') -join "`n"
        Write-Utf8NoBom -Path $wrapper -Content ($lines + "`n")
        $exe = '/bin/sh'; $args = "`"$wrapper`""
    }
    $proc = Start-Process -FilePath $exe -ArgumentList $args `
        -RedirectStandardOutput $OutFile -RedirectStandardError $ErrFile `
        -WorkingDirectory $WorkDir -NoNewWindow -PassThru
    # Capturar el handle ANTES de esperar: sin esto ExitCode queda null (quirk .NET).
    $null = $proc.Handle
    $exited = $proc.WaitForExit($TimeoutSeconds * 1000)
    if (-not $exited) {
        Stop-ProcessTree -Process $proc
        return [pscustomobject]@{ exitCode = -1; timedOut = $true }
    }
    [pscustomobject]@{ exitCode = $proc.ExitCode; timedOut = $false }
}
