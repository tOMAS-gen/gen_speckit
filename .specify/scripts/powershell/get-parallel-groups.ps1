#Requires -Version 5.1
<#
.SYNOPSIS
  Agrupa las tareas pendientes de un tasks.md en tandas de ejecucion: las [P] sin
  rutas compartidas corren en paralelo (con limite de concurrencia); los conflictos
  de archivo y las tareas sin rutas declaradas se serializan (FR-017).
.NOTES
  Dot-source para importar funciones sin ejecutar (tests).
  Salida: JSON con la lista ordenada de grupos.
#>
[CmdletBinding()]
param(
    [string]$TasksPath,
    [int]$MaxConcurrency = 4
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

# Regex del contrato task-labels.md (grupos: id, P, US, complejidad, cli, modelo, descripcion)
$script:TaskLineRegex = '^\s*- \[( |x|X)\] +(T\d{3,}) +(?:(\[P\]) +)?(?:(\[US\d+\]) +)?(?:\[C:(baja|media|alta)\] +)?(?:\[M:([a-z][a-z0-9-]*)/([A-Za-z0-9._-]+)\] +)?(.+)$'

function ConvertFrom-TaskLine {
    # Parsea una linea de tasks.md; devuelve $null si no es una linea de tarea.
    param([string]$Line)
    $m = [regex]::Match($Line, $script:TaskLineRegex)
    if (-not $m.Success) { return $null }
    $desc = $m.Groups[8].Value.Trim()
    [pscustomobject]@{
        completada  = ($m.Groups[1].Value -ne ' ')
        id          = $m.Groups[2].Value
        paralela    = $m.Groups[3].Success
        historia    = if ($m.Groups[4].Success) { $m.Groups[4].Value.Trim('[',']') } else { $null }
        complejidad = if ($m.Groups[5].Success) { $m.Groups[5].Value } else { $null }
        cli         = if ($m.Groups[6].Success) { $m.Groups[6].Value } else { $null }
        modelo      = if ($m.Groups[7].Success) { $m.Groups[7].Value } else { $null }
        descripcion = $desc
        rutas       = @(Get-TaskPaths $desc)
    }
}

function Get-TaskPaths {
    # Extrae rutas de archivo de la descripcion: tokens con separador de directorios
    # y nombres sueltos con extension. Falsos positivos solo serializan de mas (seguro).
    param([string]$Descripcion)
    $paths = New-Object System.Collections.Generic.List[string]
    $withSep = [regex]::Matches($Descripcion, '(?:[A-Za-z0-9_.\-]+[\\/])+[A-Za-z0-9_.\-]+')
    foreach ($m in $withSep) { $paths.Add(($m.Value -replace '\\', '/').ToLowerInvariant()) }
    $bare = [regex]::Matches($Descripcion, '(?<![\\/\w.])[A-Za-z0-9_\-]+\.[A-Za-z]{1,6}(?![\\/\w])')
    foreach ($m in $bare) {
        $v = $m.Value.ToLowerInvariant()
        if (-not ($paths | Where-Object { $_.EndsWith("/$v") -or $_ -eq $v })) { $paths.Add($v) }
    }
    $paths | Select-Object -Unique
}

function Get-ParallelGroups {
    # Tandas ordenadas: cada grupo paralelo junta tareas [P] consecutivas sin rutas
    # compartidas, hasta MaxConcurrency. Todo lo demas va en grupos de a una.
    # (Sin funciones anidadas: el scoping dinamico de PS + listas genericas falla.)
    param(
        [object[]]$Tareas,       # salida de ConvertFrom-TaskLine, solo pendientes
        [int]$MaxConcurrency = 4
    )
    $grupos = New-Object System.Collections.ArrayList
    $actual = New-Object System.Collections.ArrayList
    $rutasEnUso = New-Object System.Collections.ArrayList

    foreach ($t in $Tareas) {
        $esParalelizable = $t.paralela -and (@($t.rutas).Count -gt 0)
        $conflicto = $false
        if ($esParalelizable) {
            foreach ($r in $t.rutas) { if ($rutasEnUso -contains $r) { $conflicto = $true; break } }
        }
        # Cerrar el grupo en curso si esta tarea no puede sumarse.
        if (((-not $esParalelizable) -or $conflicto -or $actual.Count -ge $MaxConcurrency) -and $actual.Count -gt 0) {
            [void]$grupos.Add([pscustomobject]@{ paralelo = ($actual.Count -gt 1); tareas = @($actual.ToArray()) })
            $actual.Clear(); $rutasEnUso.Clear()
        }
        if ($esParalelizable) {
            [void]$actual.Add($t)
            foreach ($r in $t.rutas) { [void]$rutasEnUso.Add($r) }
        } else {
            # No-[P] o sin rutas declaradas (conflicto potencial): serializar (FR-017).
            [void]$grupos.Add([pscustomobject]@{ paralelo = $false; tareas = @($t) })
        }
    }
    if ($actual.Count -gt 0) {
        [void]$grupos.Add([pscustomobject]@{ paralelo = ($actual.Count -gt 1); tareas = @($actual.ToArray()) })
    }
    ,@($grupos.ToArray())
}

function Invoke-GetParallelGroups {
    param([string]$TasksPath, [int]$MaxConcurrency)
    if (-not (Test-Path $TasksPath)) { throw "No existe tasks.md en: $TasksPath" }
    $todas = @(Get-Content $TasksPath | ForEach-Object { ConvertFrom-TaskLine $_ } | Where-Object { $null -ne $_ })
    $pendientes = @($todas | Where-Object { -not $_.completada })
    $grupos = Get-ParallelGroups -Tareas $pendientes -MaxConcurrency $MaxConcurrency
    $resumen = [ordered]@{
        total_tareas      = $todas.Count
        pendientes        = $pendientes.Count
        sin_asignar       = @($pendientes | Where-Object { $null -eq $_.modelo }).Count
        max_concurrencia  = $MaxConcurrency
        grupos            = @($grupos | ForEach-Object {
            [ordered]@{
                paralelo = $_.paralelo
                tareas   = @($_.tareas | ForEach-Object {
                    [ordered]@{
                        id = $_.id; complejidad = $_.complejidad
                        cli = $_.cli; modelo = $_.modelo
                        rutas = @($_.rutas); descripcion = $_.descripcion
                    }
                })
            }
        })
    }
    ConvertTo-Json -InputObject $resumen -Depth 6
}

if ($MyInvocation.InvocationName -ne '.') {
    if (-not $TasksPath) { throw 'Falta -TasksPath' }
    Invoke-GetParallelGroups -TasksPath $TasksPath -MaxConcurrency $MaxConcurrency
}
