@echo OFF

SET files=venv .vs .idea
for %%a in (%files%) do (
    IF EXIST ./%%a (
            rmdir %%a /Q /S
    )
)
