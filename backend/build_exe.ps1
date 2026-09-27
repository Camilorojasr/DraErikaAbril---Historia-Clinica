# Genera dist\Vitalis.exe: backend + frontend empaquetados en un solo archivo portable.
# Uso: abrir PowerShell en la carpeta backend/ y correr:  .\build_exe.ps1
.\venv\Scripts\python.exe -m PyInstaller --noconfirm --onefile --console --name Vitalis --add-data "..\vitalis-frontend.html;." launcher.py
Write-Host ""
Write-Host "Listo: dist\Vitalis.exe" -ForegroundColor Green
Write-Host "Copia ese unico archivo al computador de destino y ejecutalo con doble clic." -ForegroundColor Green
