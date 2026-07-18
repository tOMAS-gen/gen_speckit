#Requires -Version 5.1
<#
.SYNOPSIS
  Actualiza el estado de cuota de un CLI en .specify/models.json. Es la UNICA
  escritura automatica permitida sobre el inventario (FR-018): solo toca los campos
  cuota, cuota_desde y cuota_reset del CLI indicado; el resto queda intacto.
.NOTES
  Reusa el serializador canonico de scan-models.ps1 (UTF-8 sin BOM, indentacion 2).
  Dot-source para importar funciones sin ejecutar (tests).
#>
[CmdletBinding()]
param(
    [string]$Cli,
    [ValidateSet('agotada', 'ok')]
    [string]$Estado,
    [string]$ModelsPath
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

# Reusar ConvertTo-PlainValue / ConvertTo-Json2Space / Write-Utf8NoBom (mismo formato canonico).
. (Join-Path (Split-Path -Parent $PSCommandPath) 'scan-models.ps1')

function Get-QuotaReset {
    # Estima la fecha de reset segun la ventana declarada del plan.
    # Plan desconocido o sin ventana parseable -> 'desconocido' (persiste hasta reset manual).
    param([string]$Plan, [datetime]$Desde)
    if ([string]::IsNullOrWhiteSpace($Plan) -or $Plan -eq 'desconocido') { return 'desconocido' }
    if ($Plan -imatch '(\d+)\s*h') { return ($Desde.AddHours([int]$Matches[1])).ToString('yyyy-MM-ddTHH:mm:sszzz') }
    if ($Plan -imatch 'sem|week')  { return ($Desde.AddDays(7)).ToString('yyyy-MM-ddTHH:mm:sszzz') }
    if ($Plan -imatch 'd[ii]a|day|daily|diari') { return ($Desde.AddDays(1)).ToString('yyyy-MM-ddTHH:mm:sszzz') }
    if ($Plan -imatch 'mes|month') { return ($Desde.AddDays(30)).ToString('yyyy-MM-ddTHH:mm:sszzz') }
    'desconocido'
}

function Update-Quota {
    param(
        [string]$ModelsPath,
        [string]$Cli,
        [string]$Estado,
        [datetime]$Now = (Get-Date)
    )
    if (-not (Test-Path $ModelsPath)) { throw "No existe el inventario: $ModelsPath" }
    $data = ConvertTo-PlainValue (Get-Content $ModelsPath -Raw | ConvertFrom-Json)
    if (-not $data.Contains('clis') -or -not $data['clis'].Contains($Cli)) {
        throw "CLI '$Cli' no existe en el inventario"
    }
    $entry = $data['clis'][$Cli]

    if ($Estado -eq 'agotada') {
        $entry['cuota'] = 'agotada'
        $entry['cuota_desde'] = $Now.ToString('yyyy-MM-ddTHH:mm:sszzz')
        $plan = if ($entry.Contains('plan')) { [string]$entry['plan'] } else { 'desconocido' }
        $entry['cuota_reset'] = Get-QuotaReset -Plan $plan -Desde $Now
    } else {
        $entry['cuota'] = 'ok'
        if ($entry.Contains('cuota_desde')) { $entry.Remove('cuota_desde') }
        if ($entry.Contains('cuota_reset')) { $entry.Remove('cuota_reset') }
    }

    Write-Utf8NoBom -Path $ModelsPath -Content (ConvertTo-Json2Space $data)
    [pscustomobject]@{
        cli = $Cli; cuota = $entry['cuota']
        cuota_reset = if ($entry.Contains('cuota_reset')) { $entry['cuota_reset'] } else { $null }
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    foreach ($req in @('Cli', 'Estado', 'ModelsPath')) {
        if (-not (Get-Variable $req -ValueOnly)) { throw "Falta -$req" }
    }
    $r = Update-Quota -ModelsPath $ModelsPath -Cli $Cli -Estado $Estado
    Write-Host "Cuota de '$($r.cli)' -> $($r.cuota)$(if ($r.cuota_reset) { " (reset estimado: $($r.cuota_reset))" })"
    exit 0
}
