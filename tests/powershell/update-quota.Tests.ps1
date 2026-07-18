# Tests Pester 5 para update-quota.ps1
BeforeAll {
    $repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    . (Join-Path $repoRoot '.specify\scripts\powershell\update-quota.ps1')

    function New-SampleModels {
        $json = @'
{
  "clis": {
    "kimi": {
      "instalado": true,
      "autenticado": true,
      "version": "1.0",
      "headless": "kimi --print --yolo --command \"{prompt}\"",
      "plan": "5h",
      "cuota": "ok",
      "modelos": [
        {
          "id": "k2",
          "capacidad": 6,
          "costo": 1,
          "contexto_k": 256
        }
      ]
    }
  },
  "asignacion": {
    "alta": ["kimi/k2"],
    "media": ["kimi/k2"],
    "baja": ["kimi/k2"]
  }
}
'@
        $path = Join-Path $TestDrive "models-$([guid]::NewGuid().ToString('N').Substring(0,8)).json"
        Set-Content -Path $path -Value $json -Encoding UTF8
        $path
    }
}

Describe 'Get-QuotaReset' {

    BeforeAll {
        $desde = Get-Date '2026-07-18T10:00:00'
    }

    It 'plan con ventana en horas suma esas horas' {
        Get-QuotaReset -Plan '5h' -Desde $desde | Should -Match '^2026-07-18T15:00:00'
    }

    It 'plan semanal suma 7 dias' {
        Get-QuotaReset -Plan 'Pro semanal' -Desde $desde | Should -Match '^2026-07-25T10:00:00'
    }

    It 'plan desconocido devuelve desconocido (Clarificacion S3 + invariante 7)' {
        Get-QuotaReset -Plan 'desconocido' -Desde $desde | Should -Be 'desconocido'
        Get-QuotaReset -Plan '' -Desde $desde | Should -Be 'desconocido'
    }
}

Describe 'Update-Quota (escritura acotada, FR-018)' {

    It 'marca agotada con cuota_desde y cuota_reset estimado por el plan' {
        $path = New-SampleModels
        $now = Get-Date '2026-07-18T10:00:00'
        Update-Quota -ModelsPath $path -Cli 'kimi' -Estado 'agotada' -Now $now | Out-Null
        $d = Get-Content $path -Raw | ConvertFrom-Json
        $d.clis.kimi.cuota | Should -Be 'agotada'
        # Sobre el JSON crudo: pwsh 7 convierte strings de fecha a [datetime] al
        # parsear y el -Match compararia contra la forma culturizada (quirk real de CI).
        $raw = Get-Content $path -Raw
        $raw | Should -Match '"cuota_desde": "2026-07-18T10:00:00'
        $raw | Should -Match '"cuota_reset": "2026-07-18T15:00:00'
    }

    It 'NO toca ningun otro campo del inventario' {
        $path = New-SampleModels
        Update-Quota -ModelsPath $path -Cli 'kimi' -Estado 'agotada' | Out-Null
        $d = Get-Content $path -Raw | ConvertFrom-Json
        $d.clis.kimi.plan | Should -Be '5h'
        $d.clis.kimi.version | Should -Be '1.0'
        $d.clis.kimi.modelos[0].capacidad | Should -Be 6
        $d.clis.kimi.headless | Should -Match 'yolo'
        @($d.asignacion.baja).Count | Should -Be 1
    }

    It 'estado ok limpia cuota_desde y cuota_reset' {
        $path = New-SampleModels
        Update-Quota -ModelsPath $path -Cli 'kimi' -Estado 'agotada' | Out-Null
        Update-Quota -ModelsPath $path -Cli 'kimi' -Estado 'ok' | Out-Null
        $raw = Get-Content $path -Raw
        $d = $raw | ConvertFrom-Json
        $d.clis.kimi.cuota | Should -Be 'ok'
        $raw | Should -Not -Match 'cuota_desde'
        $raw | Should -Not -Match 'cuota_reset'
    }

    It 'falla con un CLI inexistente' {
        $path = New-SampleModels
        { Update-Quota -ModelsPath $path -Cli 'codex' -Estado 'agotada' } | Should -Throw
    }

    It 'la salida sigue siendo UTF-8 sin BOM' {
        $path = New-SampleModels
        Update-Quota -ModelsPath $path -Cli 'kimi' -Estado 'agotada' | Out-Null
        $bytes = [System.IO.File]::ReadAllBytes($path)
        # Un BOM UTF-8 empezaria con EF BB BF
        ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB) | Should -Be $false
    }
}
