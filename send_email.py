import argparse
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import List, Dict, Any

try:
	from dotenv import load_dotenv
except ImportError:
	load_dotenv = None  # type: ignore


def load_env_variables() -> None:
	if load_dotenv is not None:
		# Carrega variáveis do .env se existir
		env_path = Path(__file__).with_name('.env')
		if env_path.exists():
			load_dotenv(env_path)


def read_config(config_path: Path) -> Dict[str, Any]:
	with config_path.open('r', encoding='utf-8') as f:
		return json.load(f)


def build_email_message(from_name: str, sender_email: str, entry: Dict[str, Any]) -> EmailMessage:
	to_list: List[str] = entry.get('to') or []
	cc_list: List[str] = entry.get('cc') or []
	bcc_list: List[str] = entry.get('bcc') or []
	subject: str = entry.get('subject') or ''
	body: str = entry.get('body') or ''

	if not to_list:
		raise ValueError('Lista de destinatários "to" está vazia em uma das mensagens no config.')

	msg = EmailMessage()
	from_header = f"{from_name} <{sender_email}>" if from_name else sender_email
	msg['From'] = from_header
	msg['To'] = ', '.join(to_list)
	if cc_list:
		msg['Cc'] = ', '.join(cc_list)
	msg['Subject'] = subject
	msg.set_content(body)
	msg.__dict__['all_recipients'] = to_list + cc_list + bcc_list  # type: ignore
	return msg


def send_via_gmail(message: EmailMessage, sender_email: str, app_password: str, dry_run: bool = False, label: str = '') -> None:
	smtp_server = 'smtp.gmail.com'
	smtp_port = 587

	all_recipients: List[str] = message.__dict__.get('all_recipients', [])  # type: ignore

	if dry_run:
		print('--- DRY RUN ---')
		if label:
			print(f'Item: {label}')
		print(f'From: {message["From"]}')
		print(f'To: {message.get("To", "")}')
		print(f'Cc: {message.get("Cc", "")}')
		print(f'Subject: {message.get("Subject", "")}')
		print(f'Recipients to send: {", ".join(all_recipients)}')
		print('Body:')
		print(message.get_content())
		print('--- END DRY RUN ---')
		return

	context = ssl.create_default_context()
	with smtplib.SMTP(smtp_server, smtp_port) as server:
		server.ehlo()
		server.starttls(context=context)
		server.ehlo()
		server.login(sender_email, app_password)
		server.send_message(message, from_addr=sender_email, to_addrs=all_recipients)
		print(f'E-mail enviado com sucesso para {len(all_recipients)} destinatário(s).')


def main() -> None:
	parser = argparse.ArgumentParser(description='Enviar e-mail via Gmail SMTP (suporta envio único ou em lote).')
	parser.add_argument('--config', type=str, default=str(Path(__file__).with_name('config_email.json')), help='Caminho do arquivo de configuração JSON')
	parser.add_argument('--dry-run', action='store_true', help='Não envia. Mostra o que seria enviado.')
	args = parser.parse_args()

	load_env_variables()

	sender_email_env = os.getenv('EMAIL_ADDRESS')
	app_password_env = os.getenv('EMAIL_APP_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD')

	config = read_config(Path(args.config))
	from_name = config.get('from_name') or ''

	# Para dry-run, permitimos ausência das variáveis; usamos um remetente fictício se necessário
	if args.dry_run:
		sender_email = sender_email_env or 'no-reply@example.com'
		app_password = app_password_env or ''
	else:
		if not sender_email_env:
			raise SystemExit('Variável de ambiente EMAIL_ADDRESS não definida. Configure no .env.')
		if not app_password_env:
			raise SystemExit('Variável de ambiente EMAIL_APP_PASSWORD (ou GMAIL_APP_PASSWORD) não definida. Configure no .env.')
		sender_email = sender_email_env
		app_password = app_password_env  # type: ignore

	messages_config = config.get('messages')
	if isinstance(messages_config, list) and messages_config:
		# Envio em lote
		for idx, entry in enumerate(messages_config, start=1):
			msg = build_email_message(from_name, sender_email, entry)
			label = f"{idx}/{len(messages_config)}"
			send_via_gmail(msg, sender_email, app_password, dry_run=args.dry_run, label=label)
	else:
		# Compatibilidade com formato antigo (campos no topo)
		legacy_entry = {
			'to': config.get('to'),
			'cc': config.get('cc'),
			'bcc': config.get('bcc'),
			'subject': config.get('subject'),
			'body': config.get('body'),
		}
		msg = build_email_message(from_name, sender_email, legacy_entry)
		send_via_gmail(msg, sender_email, app_password, dry_run=args.dry_run)


if __name__ == '__main__':
	main()

