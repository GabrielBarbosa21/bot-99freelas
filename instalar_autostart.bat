@echo off
title Bot 99Freelas - Instalar Inicializacao Automatica
echo =========================================================
echo  INSTALANDO INICIALIZACAO AUTOMATICA NO WINDOWS (24/7)
echo =========================================================
echo.

set SCRIPT_DIR=%~dp0
set VBS_TARGET=%SCRIPT_DIR%iniciar_silencioso.vbs
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SHORTCUT_PATH=%STARTUP_DIR%\Bot99Freelas_24h.lnk

echo Criando atalho no Startup do Windows...
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = 'wscript.exe'; $s.Arguments = '\"%VBS_TARGET%\"'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.Save()"

if exist "%SHORTCUT_PATH%" (
    echo.
    echo [SUCESSO] Inicializacao automatica configurada com sucesso!
    echo O Bot 99Freelas e Painel Web iniciarao silenciosamente no boot do Windows.
    echo Atalho: %SHORTCUT_PATH%
) else (
    echo.
    echo [ERRO] Nao foi possivel criar o atalho na pasta de inicializacao.
)
echo.
pause
