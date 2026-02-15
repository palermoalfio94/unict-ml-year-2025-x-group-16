@echo off
setlocal enabledelayedexpansion

REM ================================
REM MODIFICA QUI IL PREFISSO DEL BATCH
REM esempio: b1, b2, b3, b4...
set BATCH_PREFIX=b1
REM ================================

REM Cicla tutti i file nella cartella corrente
for %%F in (*) do (
    REM Evita di rinominare il file .bat stesso
    if /I not "%%~nxF"=="%~nx0" (
        ren "%%F" "%BATCH_PREFIX%_%%F"
    )
)

echo Rinomina completata.
pause
