# Tests Pester 3.x para invoke-secondary.ps1
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent (Split-Path -Parent $here)
. (Join-Path $repoRoot '.specify\scripts\powershell\invoke-secondary.ps1')

function New-Inventory([string]$HeadlessTemplate) {
    ('{"clis":{"fake":{"instalado":true,"headless":' + ($HeadlessTemplate | ConvertTo-Json) + ',"modelos":[{"id":"m1","capacidad":5,"costo":1}]}}}') |
        ConvertFrom-Json
}

Describe 'Get-HeadlessCommand' {

    It 'sustituye {prompt} y escapa comillas dobles' {
        $inv = New-Inventory 'fake -p "{prompt}"'
        $cmd = Get-HeadlessCommand -Inventory $inv -Cli 'fake' -Model '' -Prompt 'di "hola"'
        $cmd | Should Be 'fake -p "di \"hola\""'
    }

    It 'sustituye {modelo} cuando la plantilla lo incluye' {
        $inv = New-Inventory 'fake --model {modelo} -p "{prompt}"'
        $cmd = Get-HeadlessCommand -Inventory $inv -Cli 'fake' -Model 'm1' -Prompt 'x'
        $cmd | Should Be 'fake --model m1 -p "x"'
    }

    It 'agrega --model al final cuando la plantilla no tiene {modelo}' {
        $inv = New-Inventory 'fake -p "{prompt}"'
        $cmd = Get-HeadlessCommand -Inventory $inv -Cli 'fake' -Model 'm1' -Prompt 'x'
        $cmd | Should Be 'fake -p "x" --model m1'
    }

    It 'falla con un CLI inexistente en el inventario' {
        $inv = New-Inventory 'fake -p "{prompt}"'
        { Get-HeadlessCommand -Inventory $inv -Cli 'nope' -Model '' -Prompt 'x' } | Should Throw
    }
}

Describe 'Test-QuotaPattern (contrato headless-adapters)' {

    It 'detecta patrones de cuota de claude' {
        Test-QuotaPattern -Cli 'claude' -Text 'Error: usage limit reached for today' | Should Be $true
        Test-QuotaPattern -Cli 'claude' -Text 'HTTP 429 too many requests' | Should Be $true
    }

    It 'detecta insufficient balance de kimi (regex con comodin)' {
        Test-QuotaPattern -Cli 'kimi' -Text 'Insufficient account balance, please top up' | Should Be $true
    }

    It 'no clasifica como cuota un error comun' {
        Test-QuotaPattern -Cli 'claude' -Text 'SyntaxError: unexpected token' | Should Be $false
    }

    It 'texto vacio no es cuota' {
        Test-QuotaPattern -Cli 'claude' -Text '' | Should Be $false
    }
}

Describe 'Invoke-SecondaryTask (clasificacion con stubs reales)' {

    # Stubs .cmd en TestDrive: simulan un CLI secundario sin gastar cuota real.
    $okCmd    = Join-Path $TestDrive 'ok.cmd';    Set-Content $okCmd    "@echo trabajo hecho`r`n@exit 0" -Encoding ASCII
    $failCmd  = Join-Path $TestDrive 'fail.cmd';  Set-Content $failCmd  "@echo error interno`r`n@exit 1" -Encoding ASCII
    $quotaCmd = Join-Path $TestDrive 'quota.cmd'; Set-Content $quotaCmd "@echo rate limit exceeded`r`n@exit 1" -Encoding ASCII
    $logDir = Join-Path $TestDrive 'logs'

    It 'exit 0 se clasifica exito al primer intento' {
        $inv = New-Inventory "`"$okCmd`" {prompt}"
        $r = Invoke-SecondaryTask -Cli 'fake' -Model '' -Prompt 'x' -Inventory $inv `
            -LogDir $logDir -LogBaseName 'ok' -TimeoutSeconds 30
        $r.clasificacion | Should Be 'exito'
        $r.intentos | Should Be 1
    }

    It 'fallo persistente reintenta 1 vez y clasifica indisponible (S4)' {
        $inv = New-Inventory "`"$failCmd`" {prompt}"
        $r = Invoke-SecondaryTask -Cli 'fake' -Model '' -Prompt 'x' -Inventory $inv `
            -LogDir $logDir -LogBaseName 'fail' -TimeoutSeconds 30
        $r.clasificacion | Should Be 'indisponible'
        $r.intentos | Should Be 2
    }

    It 'patron de cuota se clasifica cuota_agotada SIN reintento' {
        $inv = New-Inventory "`"$quotaCmd`" {prompt}"
        $r = Invoke-SecondaryTask -Cli 'fake' -Model '' -Prompt 'x' -Inventory $inv `
            -LogDir $logDir -LogBaseName 'quota' -TimeoutSeconds 30
        $r.clasificacion | Should Be 'cuota_agotada'
        $r.intentos | Should Be 1
    }

    It 'deja logs de stdout por intento (auditables)' {
        Test-Path (Join-Path $logDir 'fail.intento1.out.log') | Should Be $true
        Test-Path (Join-Path $logDir 'fail.intento2.out.log') | Should Be $true
    }
}
