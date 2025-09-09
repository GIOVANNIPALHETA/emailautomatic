$project = "$env:USERPROFILE\Documents\SEGURANÇA DO TRABALHO\AUTOMATIZACAO_DE_SOLICITACAO_DE_FICHA_DE_FUNCIONARIOS"
Set-Location $project
python .\send_email.py

