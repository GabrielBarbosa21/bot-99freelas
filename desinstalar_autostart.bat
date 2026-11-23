@echo off
title Bot 99Freelas - Remover Inicializacao Automatica
echo =========================================================
echo  REMOVENDO INICIALIZACAO AUTOMATICA DO WINDOWS
echo =========================================================
echo.

set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SHORTCUT_PATH=%STARTUP_DIR%\Bot99Freelas_24h.lnk

if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%"
    echo [SUCESSO] Atalho de inicializacao automatica removido com sucesso!
) else (
    echo [AVISO] O atalho de inicializacao automatica nao estava presente.
)
echo.
pause
