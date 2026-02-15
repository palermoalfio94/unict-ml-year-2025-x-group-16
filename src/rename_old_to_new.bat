@echo off
setlocal enabledelayedexpansion

REM ===========================================
REM SOSTITUISCI QUI IL PREFISSO VECCHIO E NUOVO
set OLD_PREFIX=b1_
set NEW_PREFIX=b8_
REM ===========================================

REM Cicla tutti i file nella cartella corrente
for %%F in (%OLD_PREFIX%*) do (
    REM Crea il nuovo nome sostituendo OLD_PREFIX con NEW_PREFIX
    set "NEWNAME=%%F"
    set "NEWNAME=!NEWNAME:%OLD_PREFIX%=%NEW_PREFIX%!"
    ren "%%F" "!NEWNAME!"
)

echo Rinomina completata.
pause
