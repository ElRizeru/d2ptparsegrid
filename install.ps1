$ASCII_ART = @"
 ____  ____  ____ _____    ____ ____  ___ ____  
|  _ \|___ \|  _ \_   _|  / ___|  _ \|_ _|  _ \ 
| | | | __) | |_) || |   | |  _| |_) || || | | |
| |_| |/ __/|  __/ | |   | |_| |  _ < | || |_| |
|____/|_____|_|    |_|    \____|_| \_\___|____/ 
"@

$ITEMBUILDS_URL = "https://raw.githubusercontent.com/ElRizeru/d2ptgrid/main/itembuilds.zip"
$REPO = "ElRizeru/d2ptgrid"
$GRID_URL_TEMPLATE = "https://raw.githubusercontent.com/$REPO/main/hero_grids/{0}/hero_grid_config.json"
$CONFIG_FILE = "config.json"

$CATEGORIES = @{
    "1" = @("most_played", "Most Played")
    "2" = @("high_winrate", "Most Picked Heroes (>50% Winrate)")
    "3" = @("d2pt_rating", "D2PT Rating")
}

function Get-SteamPath {
    try {
        $path = Get-ItemProperty -Path "HKCU:\Software\Valve\Steam" -Name "SteamPath" -ErrorAction Stop
        return $path.SteamPath
    } catch {
        return "C:\Program Files (x86)\Steam"
    }
}

function Clean-OldGuides($guidePath, $remotecachePath, $newBuildFiles) {
    if (-not (Test-Path $guidePath)) { return }
    $oldFiles = @()
    foreach ($file in Get-ChildItem -Path $guidePath -Filter "*.build") {
        if ($newBuildFiles -notcontains $file.Name) {
            $content = Get-Content $file.FullName -Raw
            if ($content -match '"Title"\s+"ODG ' -or $content -match '"Title"\t"ODG ') {
                $oldFiles += $file.Name
            }
        }
    }
    
    if ($oldFiles.Count -eq 0) { return }
    
    Write-Host "Cleaning $($oldFiles.Count) old guides from $guidePath" -ForegroundColor Cyan
    foreach ($f in $oldFiles) {
        Remove-Item (Join-Path $guidePath $f) -Force -ErrorAction SilentlyContinue
    }
    
    if (Test-Path $remotecachePath) {
        $content = Get-Content $remotecachePath -Raw
        foreach ($f in $oldFiles) {
            $vdfKey = "guides/$f"
            $escapedKey = [regex]::Escape($vdfKey)
            $pattern = "`t*`"$escapedKey`"\s*\{[^}]+\}\r?\n"
            $content = $content -replace $pattern, ""
        }
        Set-Content -Path $remotecachePath -Value $content -NoNewline
    }
}

function Update-Itembuilds($steamBase) {
    $userData = Join-Path $steamBase "userdata"
    if (-not (Test-Path $userData)) {
        Write-Host "Steam userdata not found at $userData" -ForegroundColor Red
        return
    }

    Write-Host "Downloading itembuilds..." -ForegroundColor Cyan
    $tempZip = Join-Path $env:TEMP "guides_temp.zip"
    $extractPath = Join-Path $env:TEMP "extract_temp"
    
    try {
        Invoke-WebRequest -Uri $ITEMBUILDS_URL -OutFile $tempZip -UseBasicParsing
        if (Test-Path $extractPath) { Remove-Item -Recurse -Force $extractPath }
        Expand-Archive -Path $tempZip -DestinationPath $extractPath
        
        $newBuildFiles = @(Get-ChildItem -Path $extractPath -File | Select-Object -ExpandProperty Name)
        
        $steamRunning = $false
        if (Get-Process -Name "steam" -ErrorAction SilentlyContinue) {
            $steamRunning = $true
            Write-Host "Shutting down Steam to update guides..." -ForegroundColor Yellow
            $steamExe = Join-Path $steamBase "steam.exe"
            if (Test-Path $steamExe) {
                Start-Process -FilePath $steamExe -ArgumentList "-shutdown" -Wait
                Start-Sleep -Seconds 5
            } else {
                Stop-Process -Name "steam" -Force
                Start-Sleep -Seconds 5
            }
        }

        foreach ($id in Get-ChildItem $userData -Directory) {
            if ($id.Name -match "^\d+$") {
                $guideDir = Join-Path $id.FullName "570\remote\guides"
                $remotecachePath = Join-Path $id.FullName "570\remotecache.vdf"
                
                if (-not (Test-Path $guideDir)) { New-Item -ItemType Directory -Force -Path $guideDir | Out-Null }
                
                Clean-OldGuides $guideDir $remotecachePath $newBuildFiles
                
                foreach ($file in $newBuildFiles) {
                    $src = Join-Path $extractPath $file
                    $dst = Join-Path $guideDir $file
                    Copy-Item -Path $src -Destination $dst -Force
                    
                    if (Test-Path $remotecachePath) {
                        $hash = (Get-FileHash -Path $dst -Algorithm SHA1).Hash.ToLower()
                        $size = (Get-Item $dst).Length
                        $t = [int][DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
                        
                        $lines = [System.Collections.Generic.List[string]](Get-Content $remotecachePath)
                        $vdfKey = "guides/$file"
                        $found = $false
                        foreach ($line in $lines) {
                            if ($line -match [regex]::Escape($vdfKey)) { $found = $true; break }
                        }
                        
                        if (-not $found) {
                            for ($j = $lines.Count - 1; $j -ge 0; $j--) {
                                if ($lines[$j].Trim() -eq '}') {
                                    $entryLines = @(
                                        "`t`"$vdfKey`"",
                                        "`t{",
                                        "`t`t`"root`"`t`t`"0`"",
                                        "`t`t`"size`"`t`t`"$size`"",
                                        "`t`t`"localtime`"`t`t`"$t`"",
                                        "`t`t`"time`"`t`t`"$t`"",
                                        "`t`t`"remotetime`"`t`t`"$t`"",
                                        "`t`t`"sha`"`t`t`"$hash`"",
                                        "`t`t`"syncstate`"`t`t`"1`"",
                                        "`t`t`"persiststate`"`t`t`"0`"",
                                        "`t`t`"platformstosync2`"`t`t`"-1`"",
                                        "`t}"
                                    )
                                    $lines.InsertRange($j, $entryLines)
                                    break
                                }
                            }
                            Set-Content -Path $remotecachePath -Value $lines
                        }
                    }
                }
            }
        }
        
        if ($steamRunning) {
            Write-Host "Restarting Steam..." -ForegroundColor Yellow
            $steamExe = Join-Path $steamBase "steam.exe"
            if (Test-Path $steamExe) {
                Start-Process -FilePath $steamExe
            }
        }

        Write-Host "Itembuilds updated successfully." -ForegroundColor Green
    } catch {
        Write-Host "Itembuilds update failed: $_" -ForegroundColor Red
    } finally {
        if (Test-Path $tempZip) { Remove-Item -Force $tempZip }
        if (Test-Path $extractPath) { Remove-Item -Recurse -Force $extractPath }
    }
}

function Update-HeroGrids($categoryKey, $steamBase) {
    $cat = $CATEGORIES[$categoryKey]
    if (-not $cat) { $cat = $CATEGORIES["2"] }
    
    $folder = $cat[0]
    $name = $cat[1]
    $url = $GRID_URL_TEMPLATE -f $folder
    
    Write-Host "Updating grids: $name" -ForegroundColor Cyan
    $userData = Join-Path $steamBase "userdata"
    
    if (-not (Test-Path $userData)) {
        Write-Host "Steam userdata not found." -ForegroundColor Red
        return
    }

    $count = 0
    foreach ($id in Get-ChildItem $userData -Directory) {
        if ($id.Name -match "^\d+$") {
            $gridDir = Join-Path $id.FullName "570\remote\cfg"
            if (Test-Path $gridDir) {
                $target = Join-Path $gridDir "hero_grid_config.json"
                if (Test-Path $target) { Copy-Item $target "$target.bak" -Force }
                try {
                    Invoke-WebRequest -Uri $url -OutFile $target -ErrorAction Stop
                    Write-Host "Updated grid for $($id.Name)" -ForegroundColor Green
                    $count++
                } catch {
                    Write-Host "Failed to download file: $_" -ForegroundColor Red
                }
            }
        }
    }
    if ($count -eq 0) { Write-Host "No Steam profiles found." -ForegroundColor Yellow }
}

Clear-Host
Write-Host $ASCII_ART -ForegroundColor Cyan
Write-Host ("-" * 50)

$config = @{}
if (Test-Path $CONFIG_FILE) { $config = Get-Content $CONFIG_FILE | ConvertFrom-Json }

$catChoice = $config.category
$guidesChoice = $config.install_guides

if ($catChoice -and $null -ne $guidesChoice) {
    $currentCatName = $CATEGORIES[$catChoice][1]
    Write-Host "Loaded saved settings:"
    Write-Host "Category: $currentCatName"
    Write-Host "Install Guides: $(if($guidesChoice){'Yes'}else{'No'})"
    $useSaved = Read-Host "Use these settings? (y/n, default y)"
    if ($useSaved -eq "n") { $catChoice = $null; $guidesChoice = $null }
}

if (-not $catChoice) {
    Write-Host "`nSelect Hero Grid Category:"
    Write-Host "1. Most Played"
    Write-Host "2. Most Picked Heroes (>50% Winrate)"
    Write-Host "3. D2PT Rating"
    $catChoice = Read-Host "Choice (default 2)"
    if (-not $catChoice) { $catChoice = "2" }
}

if ($null -eq $guidesChoice) {
    $gInput = Read-Host "`nInstall Item Guides? (y/n, default y)"
    $guidesChoice = ($gInput -ne "n")
}

if ($config.category -ne $catChoice -or $config.install_guides -ne $guidesChoice) {
    $save = Read-Host "`nSave settings? (y/n, default n)"
    if ($save -eq "y") {
        $config.category = $catChoice
        $config.install_guides = $guidesChoice
        $config | ConvertTo-Json | Set-Content $CONFIG_FILE
    }
}

Write-Host "`nStarting update..." -ForegroundColor Cyan
$steam = Get-SteamPath

Update-HeroGrids $catChoice $steam
if ($guidesChoice) { Update-Itembuilds $steam }

Write-Host "`nUpdate complete. Press Enter to exit."
[void][System.Console]::ReadLine()
