$ErrorActionPreference='Stop'
$p='HKLM:\SOFTWARE\WOW6432Node\DelphineSoft\MotoRacer2\CurrentVersion\Moto'
New-Item -Path $p -Force | Out-Null
New-ItemProperty $p -Name DataPath -Value 'D:\' -PropertyType String -Force | Out-Null
New-ItemProperty $p -Name SavingPath -Value 'C:\Games\Moto Racer 2' -PropertyType String -Force | Out-Null
New-ItemProperty $p -Name Language -Value 'ENGLISH' -PropertyType String -Force | Out-Null
New-ItemProperty $p -Name InstallType -Value 2 -PropertyType DWord -Force | Out-Null
New-ItemProperty $p -Name Version -Value 1 -PropertyType DWord -Force | Out-Null
New-ItemProperty $p -Name PId -Value 139165301 -PropertyType DWord -Force | Out-Null
'Completed' | Set-Content 'C:\Games\mr2-registration-done.txt'
