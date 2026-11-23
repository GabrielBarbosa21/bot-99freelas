@echo off
title Bot 99Freelas - Parar Execucoes em Background
echo =========================================================
echo  ENCERRANDO PROCESSOS DO BOT 99FREELAS
echo =========================================================
echo.

echo Procurando processos python executando bot_99freelas...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*bot_99freelas*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host ('Processo encerrado: PID ' + $_.ProcessId) }"

echo.
echo Operacao concluida. Todos os monitores e paineis foram encerrados.
echo.
pause
