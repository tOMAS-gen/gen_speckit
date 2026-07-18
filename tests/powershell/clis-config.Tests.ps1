# Tests Pester 5 para clis-config.ps1
BeforeAll {
    $repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    . (Join-Path $repoRoot '.specify\scripts\powershell\clis-config.ps1')

    function New-TestInventory {
        $repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
        $subDir = Join-Path $TestDrive ([guid]::NewGuid().ToString('N').Substring(0, 8))
        $null = [System.IO.Directory]::CreateDirectory($subDir)
        Copy-Item -Path (Join-Path $repoRoot '.specify\models.json') -Destination $subDir
        Copy-Item -Path (Join-Path $repoRoot '.specify\clis-catalog.json') -Destination $subDir
        Join-Path $subDir 'models.json'
    }

    function New-PortableStub {
        param(
            [string]$BasePath,
            [string]$WindowsContent,
            [string]$UnixContent,
            [switch]$Executable
        )
        $os = Get-OsFamily
        if ($os -eq 'windows') {
            $stubPath = "$BasePath.cmd"
            Set-Content -Path $stubPath -Value $WindowsContent -Encoding ASCII
        } else {
            $stubPath = $BasePath
            [System.IO.File]::WriteAllText($stubPath, "#!/bin/sh`n$UnixContent`n")
            if ($Executable) { chmod +x $stubPath }
        }
        $stubPath
    }
}

Describe 'Add-CliDefinition - validaciones' {

    It 'V1: nombre con guion bajo es rechazado' {
        $path = New-TestInventory
        {
            Add-CliDefinition -ModelsPath $path -Nombre 'bad_name' -Headless 'x {prompt}' `
                -Modelos @(@{ id = 'm1'; capacidad = 5; costo = 1 })
        } | Should -Throw '*V1:*'
    }

    It 'V2: nombre duplicado (claude) es rechazado' {
        $path = New-TestInventory
        {
            Add-CliDefinition -ModelsPath $path -Nombre 'claude' -Headless 'x {prompt}' `
                -Modelos @(@{ id = 'm1'; capacidad = 5; costo = 1 })
        } | Should -Throw '*V2:*'
    }

    It 'V3: plantilla sin placeholder de prompt es rechazada' {
        $path = New-TestInventory
        {
            Add-CliDefinition -ModelsPath $path -Nombre 'nuevo-cli' -Headless 'x comando' `
                -Modelos @(@{ id = 'm1'; capacidad = 5; costo = 1 })
        } | Should -Throw '*V3:*'
    }

    It 'V4: dos modelos con plantilla sin placeholder de modelo ni flag --model son rechazados' {
        $path = New-TestInventory
        {
            Add-CliDefinition -ModelsPath $path -Nombre 'nuevo-cli' -Headless 'x {prompt}' `
                -Modelos @(
                    @{ id = 'm1'; capacidad = 5; costo = 1 },
                    @{ id = 'm2'; capacidad = 6; costo = 2 }
                )
        } | Should -Throw '*V4:*'
    }

    It 'V5: capacidad fuera de rango es rechazada' {
        $path = New-TestInventory
        {
            Add-CliDefinition -ModelsPath $path -Nombre 'nuevo-cli' -Headless 'x {prompt}' `
                -Modelos @(@{ id = 'm1'; capacidad = 11; costo = 1 })
        } | Should -Throw '*V5:*'
    }

    It 'V6: regex de cuota con parentesis sin cerrar es rechazada' {
        $path = New-TestInventory
        {
            Add-CliDefinition -ModelsPath $path -Nombre 'nuevo-cli' -Headless 'x {prompt}' `
                -Modelos @(@{ id = 'm1'; capacidad = 5; costo = 1 }) `
                -PatronesCuota @('(.*unclosed')
        } | Should -Throw '*V6:*'
    }

    It 'alta invalida con tres problemas a la vez incluye los tres codigos V' {
        $path = New-TestInventory
        {
            Add-CliDefinition -ModelsPath $path -Nombre 'claude' -Headless 'x' `
                -Modelos @(@{ id = 'm1'; capacidad = 11; costo = 1 })
        } | Should -Throw '*V2*V3*V5*'
    }
}

Describe 'Add-CliDefinition - alta valida' {

    It 'alta valida de stub-reg persiste con origen registrado y cuota desconocido' {
        $path = New-TestInventory
        $result = Add-CliDefinition -ModelsPath $path -Nombre 'stub-reg' -Headless 'stub-reg {prompt}' `
            -Modelos @(@{ id = 'su-modelo'; capacidad = 5; costo = 2 })

        $result.operacion | Should -Be 'agregar'
        $result.cli | Should -Be 'stub-reg'

        $data = Get-Content $path -Raw | ConvertFrom-Json
        $data.clis.'stub-reg'.origen | Should -Be 'registrado'
        $data.clis.'stub-reg'.cuota | Should -Be 'desconocido'
    }

    It 'detecta stub-reg instalado cuando su ejecutable esta en PATH y aparece en asignacion.baja' {
        $path = New-TestInventory
        $stubDir = Join-Path $TestDrive 'stubs'
        New-Item -ItemType Directory -Path $stubDir | Out-Null
        $null = New-PortableStub -BasePath (Join-Path $stubDir 'stub-reg') `
            -WindowsContent '@echo off' -UnixContent 'exit 0' -Executable
        $env:PATH = "$stubDir$([System.IO.Path]::PathSeparator)$($env:PATH)"

        $result = Add-CliDefinition -ModelsPath $path -Nombre 'stub-reg' -Headless 'stub-reg {prompt}' `
            -Modelos @(@{ id = 'su-modelo'; capacidad = 5; costo = 2 })

        $result.instalado | Should -Be $true

        $data = Get-Content $path -Raw | ConvertFrom-Json
        $data.asignacion.baja | Should -Contain 'stub-reg/su-modelo'
    }
}

Describe 'Remove-CliDefinition' {

    It 'sin -Confirmado lanza error' {
        $path = New-TestInventory
        {
            Remove-CliDefinition -ModelsPath $path -Nombre 'claude'
        } | Should -Throw '*confirmacion*'
    }

    It 'sobre claude (catalogo) marca deshabilitado true sin borrar la entrada y sus referencias desaparecen de asignacion' {
        $path = New-TestInventory
        $before = Get-Content $path -Raw | ConvertFrom-Json
        $before.asignacion.baja | Should -Contain 'claude/haiku'

        Remove-CliDefinition -ModelsPath $path -Nombre 'claude' -Confirmado | Out-Null

        $after = Get-Content $path -Raw | ConvertFrom-Json
        $after.clis.claude.deshabilitado | Should -Be $true
        $after.asignacion.baja | Should -Not -Contain 'claude/haiku'
        $after.asignacion.alta | Should -Not -Contain 'claude/fable'
    }

    It 'sobre un CLI registrado lo elimina del inventario' {
        $path = New-TestInventory
        Add-CliDefinition -ModelsPath $path -Nombre 'stub-reg' -Headless 'stub-reg {prompt}' `
            -Modelos @(@{ id = 'su-modelo'; capacidad = 5; costo = 2 }) | Out-Null

        Remove-CliDefinition -ModelsPath $path -Nombre 'stub-reg' -Confirmado | Out-Null

        $data = Get-Content $path -Raw | ConvertFrom-Json
        $data.clis.PSObject.Properties.Name | Should -Not -Contain 'stub-reg'
    }
}

Describe 'Edit-CliDefinition' {

    It 'cambia solo el campo mencionado y valida el resultado' {
        $path = New-TestInventory
        $before = Get-Content $path -Raw | ConvertFrom-Json
        $expectedCapacity = $before.clis.claude.modelos[0].capacidad

        Edit-CliDefinition -ModelsPath $path -Nombre 'claude' `
            -Headless 'claude -p "{prompt}" --model {modelo}' | Out-Null

        $after = Get-Content $path -Raw | ConvertFrom-Json
        $after.clis.claude.headless | Should -Be 'claude -p "{prompt}" --model {modelo}'
        $after.clis.claude.modelos[0].capacidad | Should -Be $expectedCapacity
    }

    It 'falla si el resultado de la edicion es invalido' {
        $path = New-TestInventory
        {
            Edit-CliDefinition -ModelsPath $path -Nombre 'claude' -Headless 'sin prompt'
        } | Should -Throw '*V3*'
    }
}

Describe 'Invoke-CliVerification' {

    It 'CLI inexistente en el sistema da nivel a fallo y niveles siguientes omitidos' {
        $path = New-TestInventory
        Add-CliDefinition -ModelsPath $path -Nombre 'cli-inexistente-xyz' `
            -Headless 'cli-inexistente-xyz {prompt}' `
            -Modelos @(@{ id = 'm1'; capacidad = 5; costo = 1 }) | Out-Null

        $diag = Invoke-CliVerification -ModelsPath $path -Nombre 'cli-inexistente-xyz'

        $diag.Count | Should -Be 3
        $diag[0].nivel | Should -Be 'a'
        $diag[0].resultado | Should -Be 'fallo'
        $diag[1].nivel | Should -Be 'b'
        $diag[1].resultado | Should -Be 'omitido'
        $diag[2].nivel | Should -Be 'c'
        $diag[2].resultado | Should -Be 'omitido'
    }

    It 'CLI stub ejecutable SIN AprobarPrueba da nivel c omitido' {
        $path = New-TestInventory
        $stubDir = Join-Path $TestDrive ('stubs-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
        New-Item -ItemType Directory -Path $stubDir | Out-Null
        $stub = New-PortableStub -BasePath (Join-Path $stubDir 'stub-echo') `
            -WindowsContent "@echo off`r`necho ok`r`nexit 0" `
            -UnixContent "echo ok`nexit 0" -Executable
        $env:PATH = "$stubDir$([System.IO.Path]::PathSeparator)$($env:PATH)"

        $headless = '"{0}" {{prompt}}' -f $stub
        Add-CliDefinition -ModelsPath $path -Nombre 'stub-echo' -Headless $headless `
            -Modelos @(@{ id = 'm1'; capacidad = 5; costo = 1 }) | Out-Null

        $diag = Invoke-CliVerification -ModelsPath $path -Nombre 'stub-echo'

        $diag.Count | Should -Be 3
        $diag[0].nivel | Should -Be 'a'
        $diag[0].resultado | Should -Be 'ok'
        $diag[1].nivel | Should -Be 'b'
        $diag[1].resultado | Should -Be 'ok'
        $diag[2].nivel | Should -Be 'c'
        $diag[2].resultado | Should -Be 'omitido'
        $diag[2].correccion | Should -Match 'AprobarPrueba'
    }

    It 'CLI stub ejecutable CON AprobarPrueba da nivel c ok y el detalle contiene el comando renderizado' {
        $path = New-TestInventory
        $stubDir = Join-Path $TestDrive ('stubs-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
        New-Item -ItemType Directory -Path $stubDir | Out-Null
        $stub = New-PortableStub -BasePath (Join-Path $stubDir 'stub-echo') `
            -WindowsContent "@echo off`r`necho ok`r`nexit 0" `
            -UnixContent "echo ok`nexit 0" -Executable
        $env:PATH = "$stubDir$([System.IO.Path]::PathSeparator)$($env:PATH)"

        $headless = '"{0}" {{prompt}}' -f $stub
        Add-CliDefinition -ModelsPath $path -Nombre 'stub-echo' -Headless $headless `
            -Modelos @(@{ id = 'm1'; capacidad = 5; costo = 1 }) | Out-Null

        $diag = Invoke-CliVerification -ModelsPath $path -Nombre 'stub-echo' -AprobarPrueba

        $diag.Count | Should -Be 3
        $diag[2].nivel | Should -Be 'c'
        $diag[2].resultado | Should -Be 'ok'
        $expectedFragment = '"{0}" responde solo: ok' -f $stub
        $diag[2].detalle | Should -Match ([regex]::Escape($expectedFragment))
    }

    It 'el inventario despues de verificar conserva plan y modelos intactos' {
        $path = New-TestInventory
        $stubDir = Join-Path $TestDrive ('stubs-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
        New-Item -ItemType Directory -Path $stubDir | Out-Null
        $stub = New-PortableStub -BasePath (Join-Path $stubDir 'stub-echo') `
            -WindowsContent "@echo off`r`necho ok`r`nexit 0" `
            -UnixContent "echo ok`nexit 0" -Executable
        $env:PATH = "$stubDir$([System.IO.Path]::PathSeparator)$($env:PATH)"

        $headless = '"{0}" {{prompt}}' -f $stub
        Add-CliDefinition -ModelsPath $path -Nombre 'stub-echo' -Headless $headless `
            -Modelos @(@{ id = 'm1'; capacidad = 5; costo = 1 }) | Out-Null

        Invoke-CliVerification -ModelsPath $path -Nombre 'stub-echo' -AprobarPrueba | Out-Null

        $data = Get-Content $path -Raw | ConvertFrom-Json
        $data.clis.'stub-echo'.plan | Should -Be 'desconocido'
        $data.clis.'stub-echo'.modelos[0].id | Should -Be 'm1'
        $data.clis.'stub-echo'.modelos[0].capacidad | Should -Be 5
    }
}
