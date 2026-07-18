#Requires -Version 5.1
<#
.SYNOPSIS
  Invoca un CLI secundario en modo headless para ejecutar una tarea, con timeout,
  1 reintento ante fallo transitorio y clasificacion del resultado
  (exito | cuota_agotada | indisponible) segun contracts/headless-adapters.md.
.NOTES
  El comando concreto SIEMPRE sale de la plantilla headless de .specify/models.json.
  Dot-source para importar funciones sin ejecutar (tests).
#>
[CmdletBinding()]
param(
    [string]$Cli,
    [string]$Model,
    [string]$Prompt,
    [string]$ModelsPath,
    [string]$LogDir,
    [string]$LogBaseName = 'tarea',
    [int]$TimeoutSeconds = 900,   # 15 min por defecto (FR-016)
    [string]$WorkingDirectory = (Get-Location).Path
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

# Patrones de cuota agotada por CLI (contracts/headless-adapters.md; extensibles).
$script:QuotaPatterns = @{
    claude = @('usage limit', 'rate limit', 'quota', 'limit reached', '\b429\b')
    codex  = @('rate limit', 'usage', 'quota exceeded', '\b429\b', 'plan limit')
    kimi   = @('rate limit', 'quota', '\b429\b', 'insufficient.*balance')
}

function Get-HeadlessCommand {
    # Construye el comando concreto desde la plantilla del inventario.
    param($Inventory, [string]$Cli, [string]$Model, [string]$Prompt)
    $entry = $Inventory.clis.$Cli
    if ($null -eq $entry) { throw "CLI '$Cli' no existe en el inventario" }
    $template = $entry.headless
    if ([string]::IsNullOrWhiteSpace($template)) { throw "CLI '$Cli' no tiene plantilla headless" }
    $escapedPrompt = $Prompt -replace '"', '\"'
    $command = $template -replace '\{prompt\}', $escapedPrompt
    if ($command -match '\{modelo\}') {
        $command = $command -replace '\{modelo\}', $Model
    } elseif ($Model) {
        $command = "$command --model $Model"
    }
    $command
}

function Test-QuotaPattern {
    # $true si la salida matchea un patron de limite de uso del CLI dado.
    param([string]$Cli, [string]$Text)
    if ([string]::IsNullOrEmpty($Text)) { return $false }
    $patterns = $script:QuotaPatterns[$Cli]
    if ($null -eq $patterns) { $patterns = $script:QuotaPatterns.Values | ForEach-Object { $_ } }
    foreach ($p in $patterns) {
        if ($Text -imatch $p) { return $true }
    }
    $false
}

function Resolve-CliExecutable {
    # El wrapper corre en cmd.exe, cuyo PATH puede no incluir los CLIs instalados en
    # rutas de usuario (exit 9009). Se reemplaza el primer token por la ruta completa
    # de un ejecutable compatible con cmd (.exe/.cmd/.bat), si se puede resolver.
    param([string]$Cli, [string]$Command)
    # Caso especial: el shim npm de codex llama a `node` por nombre (falla cuando la
    # resolucion por PATH esta restringida). El paquete trae un binario nativo: usarlo.
    if ($Cli -eq 'codex') {
        $native = Get-ChildItem "$env:APPDATA\npm\node_modules\@openai\codex" -Recurse -Filter 'codex.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -ne $native) {
            return ($Command -replace "^\s*$([regex]::Escape($Cli))(?=\s)", "`"$($native.FullName)`"")
        }
    }
    $candidates = @("$Cli.exe", "$Cli.cmd", "$Cli.bat", $Cli)
    foreach ($c in $candidates) {
        $info = Get-Command $c -ErrorAction SilentlyContinue | Where-Object { $_.Source -match '\.(exe|cmd|bat)$' } | Select-Object -First 1
        if ($null -ne $info) {
            return ($Command -replace "^\s*$([regex]::Escape($Cli))(?=\s)", "`"$($info.Source)`"")
        }
    }
    $Command   # sin resolucion: se intenta tal cual (el fallo se clasificara normalmente)
}

function Invoke-HeadlessOnce {
    # Una invocacion con timeout; stdout/stderr capturados a archivos (auditables).
    # El comando corre via un wrapper .cmd: evita las reglas de comillas de `cmd /c`
    # con rutas/argumentos entrecomillados, y deja el comando exacto como evidencia.
    param([string]$Command, [int]$TimeoutSeconds, [string]$OutFile, [string]$ErrFile, [string]$WorkDir)
    $wrapper = "$OutFile.cmd"
    $batchCommand = $Command -replace '%', '%%'
    # El wrapper hereda el PATH completo de esta sesion: los shims (npm codex.cmd ->
    # node) y CLIs de usuario no siempre estan en el PATH del cmd hijo.
    $pathLine = 'set "PATH=' + ($env:PATH -replace '%', '%%') + '"'
    # `< NUL` cierra stdin (EOF inmediato): codex exec queda esperando stdin si el
    # handle queda abierto y silencioso.
    Set-Content -Path $wrapper -Value "@echo off`r`n$pathLine`r`n$batchCommand < NUL`r`nexit /b %ERRORLEVEL%" -Encoding Default
    $proc = Start-Process -FilePath 'cmd.exe' -ArgumentList "/d /c `"$wrapper`"" `
        -RedirectStandardOutput $OutFile -RedirectStandardError $ErrFile `
        -WorkingDirectory $WorkDir -NoNewWindow -PassThru
    # Capturar el handle ANTES de esperar: sin esto, .NET no expone ExitCode si el
    # proceso ya termino (quedaria null y todo se clasificaria mal).
    $null = $proc.Handle
    $exited = $proc.WaitForExit($TimeoutSeconds * 1000)
    if (-not $exited) {
        # Matar el ARBOL de procesos: Kill() solo mata cmd.exe y deja huerfano al CLI.
        try { & taskkill /T /F /PID $proc.Id 2>$null | Out-Null } catch { try { $proc.Kill() } catch { } }
        return [pscustomobject]@{ exitCode = -1; timedOut = $true }
    }
    [pscustomobject]@{ exitCode = $proc.ExitCode; timedOut = $false }
}

function Invoke-SecondaryTask {
    <#
      Ciclo completo (Clarificacion S4 + FR-018):
        intento 1 -> exito | cuota_agotada (sin reintento) | fallo transitorio
        fallo transitorio -> intento 2 -> exito | cuota_agotada | indisponible
    #>
    param(
        [string]$Cli, [string]$Model, [string]$Prompt,
        $Inventory,
        [string]$LogDir, [string]$LogBaseName = 'tarea',
        [int]$TimeoutSeconds = 900,
        [string]$WorkingDirectory = (Get-Location).Path
    )
    if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Force -Path $LogDir | Out-Null }
    $command = Get-HeadlessCommand -Inventory $Inventory -Cli $Cli -Model $Model -Prompt $Prompt
    $command = Resolve-CliExecutable -Cli $Cli -Command $command

    $intentos = 0
    $clasificacion = $null
    $lastExit = $null
    $outFile = $null; $errFile = $null

    while ($intentos -lt 2) {
        $intentos++
        $outFile = Join-Path $LogDir "$LogBaseName.intento$intentos.out.log"
        $errFile = Join-Path $LogDir "$LogBaseName.intento$intentos.err.log"
        $r = Invoke-HeadlessOnce -Command $command -TimeoutSeconds $TimeoutSeconds `
            -OutFile $outFile -ErrFile $errFile -WorkDir $WorkingDirectory
        $lastExit = $r.exitCode
        $texto = ''
        if (Test-Path $outFile) { $texto += (Get-Content $outFile -Raw) }
        if (Test-Path $errFile) { $texto += "`n" + (Get-Content $errFile -Raw) }

        if (-not $r.timedOut -and $r.exitCode -eq 0) { $clasificacion = 'exito'; break }
        if (Test-QuotaPattern -Cli $Cli -Text $texto) { $clasificacion = 'cuota_agotada'; break }
        # Fallo transitorio (timeout incluido): 1 reintento; al segundo, indisponible.
        if ($intentos -ge 2) { $clasificacion = 'indisponible' }
    }

    [pscustomobject]@{
        clasificacion = $clasificacion
        intentos      = $intentos
        exitCode      = $lastExit
        stdoutPath    = $outFile
        stderrPath    = $errFile
        comando       = $command
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    foreach ($req in @('Cli', 'Prompt', 'ModelsPath', 'LogDir')) {
        if (-not (Get-Variable $req -ValueOnly)) { throw "Falta -$req" }
    }
    $inventory = Get-Content $ModelsPath -Raw | ConvertFrom-Json
    $result = Invoke-SecondaryTask -Cli $Cli -Model $Model -Prompt $Prompt -Inventory $inventory `
        -LogDir $LogDir -LogBaseName $LogBaseName -TimeoutSeconds $TimeoutSeconds `
        -WorkingDirectory $WorkingDirectory
    ConvertTo-Json -InputObject $result -Depth 4
    if ($result.clasificacion -ne 'exito') { exit 1 } else { exit 0 }
}
