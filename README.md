# Automação de envio mensal de e-mails (Gmail)

Este projeto envia e-mails mensais via Gmail SMTP usando Senha de App. Agora suporta envio em lote com mensagens diferentes para destinatários diferentes.

## Requisitos
- Python 3.8+
- Conta Gmail com 2FA ativado e Senha de App

## Senha de App (Gmail)
1. Ative a verificação em 2 etapas na sua conta Google.
2. Acesse Segurança > Senhas de app e gere uma senha para "Mail".
3. Guarde a senha (16 caracteres).

## Variáveis de ambiente
Copie `.env.example` para `.env` e preencha:
```
EMAIL_ADDRESS=EMAIL-EXEMPLO@GMAIL.COM
EMAIL_APP_PASSWORD=senhaexemplo
```

## Configuração
Formato recomendado (múltiplas mensagens):
```
{
  "from_name": "Setor de Segurança do Trabalho",
  "messages": [
    {
      "to": ["destinatario1@example.com"],
      "cc": [],
      "bcc": [],
      "subject": "Solicitação mensal - Unidade A",
      "body": "Texto A"
    },
    {
      "to": ["destinatario2@example.com", "destinatario3@example.com"],
      "cc": ["gestor@example.com"],
      "bcc": [],
      "subject": "Solicitação mensal - Unidade B",
      "body": "Texto B"
    }
  ]
}
```
Compatibilidade com formato antigo (mensagem única):
```
{
  "from_name": "Setor...",
  "to": ["alguem@example.com"],
  "cc": [],
  "bcc": [],
  "subject": "Assunto",
  "body": "Corpo"
}
```

## Instalação
No PowerShell, na pasta do projeto:
```
python -m pip install -r requirements.txt
```

## Uso
- Visualizar sem enviar (todas as mensagens):
```
python send_email.py --dry-run
```
- Enviar de fato:
```
python send_email.py
```

## Interface Web (Recomendado)
Para controle visual e fácil gerenciamento:

1. Instale as dependências:
```
py -3 -m pip install -r requirements.txt
```

2. Execute a interface web:
```
py -3 app.py
```

3. Acesse no navegador: `http://localhost:5000`

**Funcionalidades da Interface Web:**
- ✅ Visualizar todas as mensagens configuradas
- ✅ Adicionar/editar/remover mensagens
- ✅ Preview das mensagens antes do envio
- ✅ Envio de todos os e-mails com um clique
- ✅ Interface responsiva e intuitiva

## Agendamento mensal (Windows Task Scheduler)
1. Criar Tarefa > Gatilhos: Mensal no dia/horário desejado.
2. Ações:
   - Programa/script: `powershell.exe`
   - Argumentos: `-NoProfile -ExecutionPolicy Bypass -File "${env:USERPROFILE}\Documents\SEGURANÇA DO TRABALHO\AUTOMATIZACAO_DE_SOLICITACAO_DE_FICHA_DE_FUNCIONARIOS\run_email.ps1"`
3. Salve.

Arquivo `run_email.ps1` já incluso:
```
$project = "$env:USERPROFILE\Documents\SEGURANÇA DO TRABALHO\AUTOMATIZACAO_DE_SOLICITACAO_DE_SOLICITACAO_DE_FICHA_DE_FUNCIONARIOS"
Set-Location $project
python .\send_email.py
```

