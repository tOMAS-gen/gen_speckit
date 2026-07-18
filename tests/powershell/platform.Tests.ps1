# Tests Pester 5 para platform.ps1
BeforeAll {
    $repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    . (Join-Path $repoRoot '.specify\scripts\powershell\platform.ps1')
}

Describe 'Get-OsFamily' {
    It 'devuelve el SO actual' {
        $expected = if ($PSVersionTable.PSVersion.Major -lt 6 -or $IsWindows) { 'windows' } elseif ($IsMacOS) { 'macos' } else { 'linux' }
        Get-OsFamily | Should -Be $expected
    }
}

Describe 'Get-NullDevice' {
    It 'devuelve el dispositivo nulo del SO' {
        $expected = if ((Get-OsFamily) -eq 'windows') { 'NUL' } else { '/dev/null' }
        Get-NullDevice | Should -Be $expected
    }
}

Describe 'Expand-PortablePath' {
    It 'expande ~ y normaliza separadores al del SO' {
        $result = Expand-PortablePath '~/x/y'
        $expected = [System.IO.Path]::Combine($HOME, 'x', 'y')
        $result | Should -Be $expected
    }

    It 'expande variables de entorno estilo %VAR%' {
        # Variable propia del test: %USERPROFILE% no existe en linux/macos.
        $env:GEN_SPECKIT_TEST_DIR = $HOME
        try {
            $result = Expand-PortablePath '%GEN_SPECKIT_TEST_DIR%\foo\bar'
            $expected = [System.IO.Path]::Combine($HOME, 'foo', 'bar')
            $result | Should -Be $expected
        } finally {
            Remove-Item Env:GEN_SPECKIT_TEST_DIR -ErrorAction SilentlyContinue
        }
    }

    It 'normaliza tanto / como \ al separador del SO' {
        $result = Expand-PortablePath 'a/b\c/d'
        $sep = [System.IO.Path]::DirectorySeparatorChar
        $result | Should -Be "a${sep}b${sep}c${sep}d"
    }
}

Describe 'Resolve-Executable' {
    It 'devuelve el hint cuando apunta a un archivo existente' {
        $os = Get-OsFamily
        $extension = if ($os -eq 'windows') { '.cmd' } else { '.sh' }
        $stub = Join-Path $TestDrive ("miexe$extension")
        New-Item -Path $stub -ItemType File | Out-Null
        if ($os -ne 'windows') {
            [System.IO.File]::WriteAllText($stub, "#!/bin/sh`n")
            chmod +x $stub
        }
        Resolve-Executable -Name 'noexiste' -ExeHints @($stub) | Should -Be $stub
    }

    It 'devuelve null para nombre inexistente sin hints' {
        Resolve-Executable -Name 'estecomandonoexiste12345' | Should -BeNullOrEmpty
    }
}

Describe 'Invoke-PortableProcess' {

    BeforeAll {
        function New-PortableStub {
            param([string]$BasePath, [string]$Content, [switch]$Executable)
            $os = Get-OsFamily
            if ($os -eq 'windows') {
                $stubPath = "$BasePath.cmd"
                Set-Content -Path $stubPath -Value $Content -Encoding ASCII
            } else {
                $stubPath = "$BasePath.sh"
                [System.IO.File]::WriteAllText($stubPath, "#!/bin/sh`n$content`n")
                if ($Executable) { chmod +x $stubPath }
            }
            $stubPath
        }
    }

    It 'ejecuta stub ok, devuelve exitCode 0 y captura salida' {
        $out = Join-Path $TestDrive 'out1.txt'
        $err = Join-Path $TestDrive 'err1.txt'
        $stubBase = Join-Path $TestDrive 'ok'
        $os = Get-OsFamily
        if ($os -eq 'windows') {
            $stub = New-PortableStub -BasePath $stubBase -Content "@echo off`necho listo`nexit 0"
        } else {
            $stub = New-PortableStub -BasePath $stubBase -Content "echo listo`nexit 0" -Executable
        }

        $result = Invoke-PortableProcess -Command $stub -TimeoutSeconds 5 -OutFile $out -ErrFile $err -WorkDir $TestDrive

        $result.exitCode | Should -Be 0
        $result.timedOut | Should -Be $false
        Get-Content $out | Should -Match 'listo'
    }

    It 'devuelve exitCode 7 para stub fallido' {
        $out = Join-Path $TestDrive 'out2.txt'
        $err = Join-Path $TestDrive 'err2.txt'
        $stubBase = Join-Path $TestDrive 'exit7'
        $os = Get-OsFamily
        if ($os -eq 'windows') {
            $stub = New-PortableStub -BasePath $stubBase -Content "@echo off`nexit 7"
        } else {
            $stub = New-PortableStub -BasePath $stubBase -Content "exit 7" -Executable
        }

        $result = Invoke-PortableProcess -Command $stub -TimeoutSeconds 5 -OutFile $out -ErrFile $err -WorkDir $TestDrive

        $result.exitCode | Should -Be 7
        $result.timedOut | Should -Be $false
    }

    It 'detecta timeout y no deja procesos colgados' {
        $out = Join-Path $TestDrive 'out3.txt'
        $err = Join-Path $TestDrive 'err3.txt'
        $stubBase = Join-Path $TestDrive 'timeout'
        $os = Get-OsFamily
        if ($os -eq 'windows') {
            $stub = New-PortableStub -BasePath $stubBase -Content "@echo off`nC:\Windows\System32\ping.exe -n 30 localhost"
            $processName = 'ping'
        } else {
            $stub = New-PortableStub -BasePath $stubBase -Content "sleep 30" -Executable
            $processName = 'sleep'
        }

        $result = Invoke-PortableProcess -Command $stub -TimeoutSeconds 2 -OutFile $out -ErrFile $err -WorkDir $TestDrive

        $result.timedOut | Should -Be $true
        Start-Sleep -Seconds 1
        Get-Process -Name $processName -ErrorAction SilentlyContinue | Should -BeNullOrEmpty
    }
}

Describe 'Stop-ProcessTree' {
    It 'mata un proceso y sus hijos' {
        $os = Get-OsFamily
        if ($os -eq 'windows') {
            $proc = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c ping -n 30 localhost' -PassThru -NoNewWindow
        } else {
            $proc = Start-Process -FilePath '/bin/sh' -ArgumentList '-c', 'sleep 30' -PassThru -NoNewWindow
        }
        try {
            Start-Sleep -Milliseconds 500
            Stop-ProcessTree -Process $proc
            $proc.HasExited | Should -Be $true
        } finally {
            if (-not $proc.HasExited) { $proc.Kill() }
        }
    }
}
