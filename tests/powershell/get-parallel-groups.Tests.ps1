# Tests Pester 3.x para get-parallel-groups.ps1
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent (Split-Path -Parent $here)
. (Join-Path $repoRoot '.specify\scripts\powershell\get-parallel-groups.ps1')

Describe 'ConvertFrom-TaskLine (regex del contrato)' {

    It 'parsea una linea completamente etiquetada' {
        $t = ConvertFrom-TaskLine '- [ ] T012 [P] [US1] [C:baja] [M:kimi/k2] Crear modelo User en src/models/user.py'
        $t.id | Should Be 'T012'
        $t.paralela | Should Be $true
        $t.historia | Should Be 'US1'
        $t.complejidad | Should Be 'baja'
        $t.cli | Should Be 'kimi'
        $t.modelo | Should Be 'k2'
        $t.completada | Should Be $false
    }

    It 'parsea una linea sin etiquetas multi-CLI (estado pre-asignacion valido)' {
        $t = ConvertFrom-TaskLine '- [ ] T031 [US3] Actualizar docs de despliegue en docs/deploy.md'
        $t.id | Should Be 'T031'
        $t.complejidad | Should BeNullOrEmpty
        $t.modelo | Should BeNullOrEmpty
    }

    It 'detecta tareas completadas [x]' {
        (ConvertFrom-TaskLine '- [x] T007 [P] [C:media] [M:codex/gpt-5-codex] Configurar linting en .eslintrc.json').completada |
            Should Be $true
    }

    It 'devuelve null para lineas que no son tareas' {
        ConvertFrom-TaskLine '## Phase 3: User Story 1' | Should BeNullOrEmpty
        ConvertFrom-TaskLine '- **[P]**: Can run in parallel' | Should BeNullOrEmpty
    }
}

Describe 'Get-TaskPaths' {

    It 'extrae rutas con separador' {
        $p = @(Get-TaskPaths 'Crear modelo User en src/models/user.py y src\services\user.py')
        $p -contains 'src/models/user.py' | Should Be $true
        $p -contains 'src/services/user.py' | Should Be $true
    }

    It 'sin rutas devuelve lista vacia' {
        @(Get-TaskPaths 'Investigar opciones de despliegue').Count | Should Be 0
    }
}

Describe 'Get-ParallelGroups (FR-017)' {

    function New-Task([string]$Line) { ConvertFrom-TaskLine $Line }

    It 'tareas [P] con archivos distintos comparten grupo paralelo' {
        $tareas = @(
            (New-Task '- [ ] T001 [P] [M:kimi/k2] Crear a en src/a.py'),
            (New-Task '- [ ] T002 [P] [M:claude/haiku] Crear b en src/b.py')
        )
        $g = Get-ParallelGroups -Tareas $tareas -MaxConcurrency 4
        @($g).Count | Should Be 1
        $g[0].paralelo | Should Be $true
        @($g[0].tareas).Count | Should Be 2
    }

    It 'tareas [P] que tocan el mismo archivo se serializan' {
        $tareas = @(
            (New-Task '- [ ] T001 [P] Editar seccion 1 de docs/readme.md'),
            (New-Task '- [ ] T002 [P] Editar seccion 2 de docs/readme.md')
        )
        $g = Get-ParallelGroups -Tareas $tareas -MaxConcurrency 4
        @($g).Count | Should Be 2
    }

    It 'una tarea [P] sin rutas declaradas se serializa (conflicto potencial)' {
        $tareas = @(
            (New-Task '- [ ] T001 [P] Crear a en src/a.py'),
            (New-Task '- [ ] T002 [P] Revisar convenciones generales'),
            (New-Task '- [ ] T003 [P] Crear c en src/c.py')
        )
        $g = Get-ParallelGroups -Tareas $tareas -MaxConcurrency 4
        @($g).Count | Should Be 3
        $g[1].paralelo | Should Be $false
    }

    It 'respeta el limite de concurrencia (default 4)' {
        $tareas = 1..5 | ForEach-Object { New-Task "- [ ] T00$_ [P] Crear f$_ en src/f$_.py" }
        $g = Get-ParallelGroups -Tareas @($tareas) -MaxConcurrency 4
        @($g).Count | Should Be 2
        @($g[0].tareas).Count | Should Be 4
        @($g[1].tareas).Count | Should Be 1
    }

    It 'una tarea sin [P] corta el grupo y va sola' {
        $tareas = @(
            (New-Task '- [ ] T001 [P] Crear a en src/a.py'),
            (New-Task '- [ ] T002 Integrar en src/main.py'),
            (New-Task '- [ ] T003 [P] Crear c en src/c.py')
        )
        $g = Get-ParallelGroups -Tareas $tareas -MaxConcurrency 4
        @($g).Count | Should Be 3
    }
}

Describe 'Invoke-GetParallelGroups (integracion sobre archivo)' {

    It 'procesa un tasks.md real y excluye completadas' {
        $sample = @(
            '# Tasks: demo',
            '- [x] T001 Setup en src/setup.py',
            '- [ ] T002 [P] [US1] [C:baja] [M:kimi/k2] Crear a en src/a.py',
            '- [ ] T003 [P] [US1] [C:baja] [M:claude/haiku] Crear b en src/b.py',
            '- [ ] T004 [US1] [C:media] [M:claude/sonnet] Integrar en src/main.py'
        ) -join "`n"
        $path = Join-Path $TestDrive 'tasks.md'
        Set-Content -Path $path -Value $sample -Encoding UTF8
        $json = Invoke-GetParallelGroups -TasksPath $path -MaxConcurrency 4
        $r = $json | ConvertFrom-Json
        $r.total_tareas | Should Be 4
        $r.pendientes | Should Be 3
        @($r.grupos).Count | Should Be 2
        $r.grupos[0].paralelo | Should Be $true
    }
}
