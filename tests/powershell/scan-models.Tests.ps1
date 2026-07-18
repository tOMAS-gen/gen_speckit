# Tests Pester 3.x para scan-models.ps1
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent (Split-Path -Parent $here)
. (Join-Path $repoRoot '.specify\scripts\powershell\scan-models.ps1')

Describe 'Build-Inventory / Build-Asignacion' {

    $detections = @{
        claude = @{ instalado = $true;  version = '2.1.0' }
        codex  = @{ instalado = $false; version = 'desconocido' }
        kimi   = @{ instalado = $true;  version = '1.4.2' }
    }
    $auth = @{ claude = $true; codex = $false; kimi = 'desconocido' }
    $clis = Build-Inventory -Detections $detections -AuthStatus $auth
    $asignacion = Build-Asignacion $clis

    It 'marca el CLI ausente como no instalado' {
        $clis['codex'].instalado | Should Be $false
    }

    It 'excluye al CLI no instalado de todas las listas de asignacion' {
        $todas = @($asignacion['alta']) + @($asignacion['media']) + @($asignacion['baja'])
        @($todas | Where-Object { $_ -like 'codex/*' }).Count | Should Be 0
    }

    It 'incluye a todos los CLIs instalados en al menos una lista (Constitucion IV)' {
        $todas = @($asignacion['alta']) + @($asignacion['media']) + @($asignacion['baja'])
        @($todas | Where-Object { $_ -like 'claude/*' }).Count | Should BeGreaterThan 0
        @($todas | Where-Object { $_ -like 'kimi/*' }).Count | Should BeGreaterThan 0
    }

    It 'deja plan y cuota como desconocido (nunca inventa valores)' {
        $clis['claude'].plan  | Should Be 'desconocido'
        $clis['claude'].cuota | Should Be 'desconocido'
    }

    It 'ordena baja por costo ascendente (el mas barato primero)' {
        $asignacion['baja'][0] | Should Match '(claude/haiku|kimi/kimi-for-coding-highspeed)'
    }

    It 'con solo kimi instalado, alta arranca con su modelo mas capaz' {
        $soloKimi = Build-Inventory -Detections @{
            claude = @{ instalado = $false; version = 'desconocido' }
            codex  = @{ instalado = $false; version = 'desconocido' }
            kimi   = @{ instalado = $true;  version = '1.0' }
        } -AuthStatus @{ claude = $false; codex = $false; kimi = $true }
        $a = Build-Asignacion $soloKimi
        $a['alta'].Count | Should BeGreaterThan 0
        $a['alta'][0] | Should Be 'kimi/k3'
    }

    It 'con nivel alta vacio usa fallback de mejores disponibles' {
        # Inventario artificial sin ningun modelo de capacidad >= 8.
        $custom = [ordered]@{
            mini = [ordered]@{
                instalado = $true
                modelos = @([ordered]@{ id = 'tiny'; capacidad = 3; costo = 1 })
            }
        }
        $a = Build-Asignacion $custom
        $a['alta'].Count | Should BeGreaterThan 0
        $a['alta'][0] | Should Be 'mini/tiny'
    }
}

Describe 'Merge-PreservingUserEdits' {

    $proposed = [ordered]@{
        clis = [ordered]@{
            claude = [ordered]@{
                plan = 'desconocido'
                modelos = @([ordered]@{ id = 'opus'; capacidad = 9; costo = 3 })
            }
        }
    }
    $prevScan = [ordered]@{
        clis = [ordered]@{
            claude = [ordered]@{
                plan = 'desconocido'
                modelos = @([ordered]@{ id = 'opus'; capacidad = 9; costo = 3 })
            }
        }
    }

    It 'una edicion manual (difiere del scan previo) prevalece sobre la propuesta nueva' {
        $existing = [ordered]@{
            clis = [ordered]@{
                claude = [ordered]@{
                    plan = 'Max 5x'   # editado por el usuario
                    modelos = @([ordered]@{ id = 'opus'; capacidad = 9; costo = 3 })
                }
            }
        }
        $merged = Merge-PreservingUserEdits -Proposed $proposed -Existing $existing -PrevScan $prevScan
        $merged.clis.claude.plan | Should Be 'Max 5x'
    }

    It 'un valor no editado se actualiza con la propuesta nueva' {
        $proposed2 = [ordered]@{
            clis = [ordered]@{
                claude = [ordered]@{
                    plan = 'desconocido'
                    modelos = @([ordered]@{ id = 'opus'; capacidad = 10; costo = 3 })
                }
            }
        }
        $existing = [ordered]@{
            clis = [ordered]@{
                claude = [ordered]@{
                    plan = 'desconocido'
                    modelos = @([ordered]@{ id = 'opus'; capacidad = 9; costo = 3 })
                }
            }
        }
        $merged = Merge-PreservingUserEdits -Proposed $proposed2 -Existing $existing -PrevScan $prevScan
        $merged.clis.claude.modelos[0].capacidad | Should Be 10
    }

    It 'sin scan previo, todo el archivo existente pertenece al usuario' {
        $existing = [ordered]@{
            clis = [ordered]@{
                claude = [ordered]@{
                    plan = 'Pro'
                    modelos = @([ordered]@{ id = 'opus'; capacidad = 5; costo = 3 })
                }
            }
        }
        $merged = Merge-PreservingUserEdits -Proposed $proposed -Existing $existing -PrevScan $null
        $merged.clis.claude.plan | Should Be 'Pro'
        $merged.clis.claude.modelos[0].capacidad | Should Be 5
    }

    It 'con -Force la propuesta nueva pisa todo' {
        $existing = [ordered]@{
            clis = [ordered]@{ claude = [ordered]@{ plan = 'Pro'; modelos = @() } }
        }
        $merged = Merge-PreservingUserEdits -Proposed $proposed -Existing $existing -PrevScan $prevScan -Force
        $merged.clis.claude.plan | Should Be 'desconocido'
    }
}

Describe 'ConvertTo-Json2Space' {

    It 'produce JSON valido con indentacion de 2 espacios' {
        $obj = [ordered]@{ a = [ordered]@{ b = 1 } }
        $out = ConvertTo-Json2Space $obj
        { $out | ConvertFrom-Json } | Should Not Throw
        ($out -split "`n" | Where-Object { $_ -match '^\s+"b"' } | Select-Object -First 1) |
            Should Match '^    "b"'   # nivel 2 -> 4 espacios (2 por nivel)
    }
}

Describe 'Salida integrada valida contra el contrato' {

    It 'toda referencia de asignacion existe en clis.<cli>.modelos' {
        $detections = @{
            claude = @{ instalado = $true;  version = 'x' }
            codex  = @{ instalado = $true;  version = 'x' }
            kimi   = @{ instalado = $true;  version = 'x' }
        }
        $auth = @{ claude = $true; codex = $true; kimi = $true }
        $clis = Build-Inventory -Detections $detections -AuthStatus $auth
        $asignacion = Build-Asignacion $clis
        foreach ($nivel in @('alta','media','baja')) {
            foreach ($ref in $asignacion[$nivel]) {
                $parts = $ref -split '/', 2
                $ids = @($clis[$parts[0]].modelos | ForEach-Object { $_.id })
                $ids -contains $parts[1] | Should Be $true
            }
        }
    }
}
