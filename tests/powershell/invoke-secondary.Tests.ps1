# Tests Pester 5 para invoke-secondary.ps1
BeforeAll {
    $script:repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    . (Join-Path $script:repoRoot '.specify\scripts\powershell\invoke-secondary.ps1')

    $script:catalog = Get-CliCatalog -RepoRoot $script:repoRoot

    function New-Inventory([string]$HeadlessTemplate) {
        ('{"clis":{"fake":{"instalado":true,"headless":' + ($HeadlessTemplate | ConvertTo-Json) + ',"modelos":[{"id":"m1","capacidad":5,"costo":1}]}}}') |
            ConvertFrom-Json
    }
}

Describe 'Get-HeadlessCommand' {

    It 'sustituye {prompt} y escapa comillas dobles' {
        $inv = New-Inventory 'fake -p "{prompt}"'
        $cmd = Get-HeadlessCommand -Inventory $inv -Cli 'fake' -Model '' -Prompt 'di "hola"'
        $cmd | Should -Be 'fake -p "di \"hola\""'
    }

    It 'sustituye {modelo} cuando la plantilla lo incluye' {
        $inv = New-Inventory 'fake --model {modelo} -p "{prompt}"'
        $cmd = Get-HeadlessCommand -Inventory $inv -Cli 'fake' -Model 'm1' -Prompt 'x'
        $cmd | Should -Be 'fake --model m1 -p "x"'
    }

    It 'agrega --model al final cuando la plantilla no tiene {modelo}' {
        $inv = New-Inventory 'fake -p "{prompt}"'
        $cmd = Get-HeadlessCommand -Inventory $inv -Cli 'fake' -Model 'm1' -Prompt 'x'
        $cmd | Should -Be 'fake -p "x" --model m1'
    }

    It 'falla con un CLI inexistente en el inventario' {
        $inv = New-Inventory 'fake -p "{prompt}"'
        { Get-HeadlessCommand -Inventory $inv -Cli 'nope' -Model '' -Prompt 'x' } | Should -Throw
    }
}

Describe 'Test-QuotaPattern (contrato headless-adapters)' {

    BeforeAll {
        $claudePatterns = Get-QuotaPatternsFor -Inventory $null -Catalog $script:catalog -Cli 'claude'
        $kimiPatterns = Get-QuotaPatternsFor -Inventory $null -Catalog $script:catalog -Cli 'kimi'
    }

    It 'detecta patrones de cuota de claude' {
        Test-QuotaPattern -Patterns $claudePatterns -Text 'Error: usage limit reached for today' | Should -Be $true
        Test-QuotaPattern -Patterns $claudePatterns -Text 'HTTP 429 too many requests' | Should -Be $true
    }

    It 'detecta insufficient balance de kimi (regex con comodin)' {
        Test-QuotaPattern -Patterns $kimiPatterns -Text 'Insufficient account balance, please top up' | Should -Be $true
    }

    It 'no clasifica como cuota un error comun' {
        Test-QuotaPattern -Patterns $claudePatterns -Text 'SyntaxError: unexpected token' | Should -Be $false
    }

    It 'texto vacio no es cuota' {
        Test-QuotaPattern -Patterns $claudePatterns -Text '' | Should -Be $false
    }
}

Describe 'Invoke-SecondaryTask (clasificacion con stubs reales)' {

    BeforeAll {
        # Stubs portables en TestDrive: simulan un CLI secundario sin gastar cuota real.
        function New-PortableStub {
            param([string]$BasePath, [string[]]$OutputLines, [int]$ExitCode = 0)
            $os = Get-OsFamily
            if ($os -eq 'windows') {
                $stubPath = "$BasePath.cmd"
                $content = (($OutputLines | ForEach-Object { "@echo $_" }) -join "`r`n") + "`r`n@exit $ExitCode"
                Set-Content -Path $stubPath -Value $content -Encoding ASCII
            } else {
                $stubPath = "$BasePath.sh"
                $content = "#!/bin/sh`n" + (($OutputLines -join "`n") + "`nexit $ExitCode`n")
                [System.IO.File]::WriteAllText($stubPath, $content)
                chmod +x $stubPath
            }
            $stubPath
        }

        $okCmd    = New-PortableStub -BasePath (Join-Path $TestDrive 'ok')    -OutputLines @('trabajo hecho')      -ExitCode 0
        $failCmd  = New-PortableStub -BasePath (Join-Path $TestDrive 'fail')  -OutputLines @('error interno')      -ExitCode 1
        $quotaCmd = New-PortableStub -BasePath (Join-Path $TestDrive 'quota') -OutputLines @('rate limit exceeded') -ExitCode 1
        $logDir = Join-Path $TestDrive 'logs'
    }

    It 'exit 0 se clasifica exito al primer intento' {
        $inv = New-Inventory "`"$okCmd`" {prompt}"
        $r = Invoke-SecondaryTask -Cli 'fake' -Model '' -Prompt 'x' -Inventory $inv `
            -LogDir $logDir -LogBaseName 'ok' -TimeoutSeconds 30
        $r.clasificacion | Should -Be 'exito'
        $r.intentos | Should -Be 1
    }

    It 'fallo persistente reintenta 1 vez y clasifica indisponible (S4)' {
        $inv = New-Inventory "`"$failCmd`" {prompt}"
        $r = Invoke-SecondaryTask -Cli 'fake' -Model '' -Prompt 'x' -Inventory $inv `
            -LogDir $logDir -LogBaseName 'fail' -TimeoutSeconds 30
        $r.clasificacion | Should -Be 'indisponible'
        $r.intentos | Should -Be 2
    }

    It 'patron de cuota se clasifica cuota_agotada SIN reintento' {
        $inv = New-Inventory "`"$quotaCmd`" {prompt}"
        $r = Invoke-SecondaryTask -Cli 'fake' -Model '' -Prompt 'x' -Inventory $inv `
            -LogDir $logDir -LogBaseName 'quota' -TimeoutSeconds 30
        $r.clasificacion | Should -Be 'cuota_agotada'
        $r.intentos | Should -Be 1
    }

    It 'deja logs de stdout por intento (auditables)' {
        Test-Path (Join-Path $logDir 'fail.intento1.out.log') | Should -Be $true
        Test-Path (Join-Path $logDir 'fail.intento2.out.log') | Should -Be $true
    }
}
