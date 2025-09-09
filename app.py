from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import os
from pathlib import Path
from send_email import send_via_gmail, build_email_message, load_env_variables

try:
    from dotenv import load_dotenv
    load_dotenv()  # Carrega automaticamente o .env
except ImportError:
    pass

# Definir variáveis diretamente se não estiverem definidas
if not os.getenv('EMAIL_ADDRESS'):
    os.environ['EMAIL_ADDRESS'] = 'COLOQUESEUEMAILAQUI@EMAIL.COM'
if not os.getenv('EMAIL_APP_PASSWORD'):
    os.environ['EMAIL_APP_PASSWORD'] = 'coloquesuasenhaappaqui'

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

CONFIG_FILE = Path(__file__).with_name('config_email.json')

def load_config():
    """Carrega configuração do arquivo JSON"""
    try:
        with CONFIG_FILE.open('r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"from_name": "", "messages": []}

def save_config(config):
    """Salva configuração no arquivo JSON"""
    with CONFIG_FILE.open('w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_env_vars():
    """Carrega variáveis do arquivo .env"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # Fallback manual se dotenv não estiver disponível
        env_path = Path(__file__).with_name('.env')
        if env_path.exists():
            with env_path.open('r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        os.environ[key] = value

@app.route('/')
def index():
    """Página principal"""
    config = load_config()
    return render_template('index.html', config=config)

@app.route('/edit_message/<int:message_id>')
def edit_message(message_id):
    """Página de edição de mensagem"""
    config = load_config()
    if 0 <= message_id < len(config.get('messages', [])):
        message = config['messages'][message_id]
        return render_template('edit_message.html', message=message, message_id=message_id)
    else:
        flash('Mensagem não encontrada!', 'error')
        return redirect(url_for('index'))

@app.route('/update_message/<int:message_id>', methods=['POST'])
def update_message(message_id):
    """Atualiza uma mensagem"""
    config = load_config()
    
    if 0 <= message_id < len(config.get('messages', [])):
        # Processar dados do formulário
        to_emails = [email.strip() for email in request.form.get('to', '').split(',') if email.strip()]
        cc_emails = [email.strip() for email in request.form.get('cc', '').split(',') if email.strip()]
        bcc_emails = [email.strip() for email in request.form.get('bcc', '').split(',') if email.strip()]
        
        config['messages'][message_id] = {
            'to': to_emails,
            'cc': cc_emails,
            'bcc': bcc_emails,
            'subject': request.form.get('subject', ''),
            'body': request.form.get('body', '')
        }
        
        config['from_name'] = request.form.get('from_name', '')
        
        save_config(config)
        flash('Mensagem atualizada com sucesso!', 'success')
    else:
        flash('Mensagem não encontrada!', 'error')
    
    return redirect(url_for('index'))

@app.route('/add_message')
def add_message():
    """Página para adicionar nova mensagem"""
    return render_template('add_message.html')

@app.route('/create_message', methods=['POST'])
def create_message():
    """Cria uma nova mensagem"""
    config = load_config()
    
    # Processar dados do formulário
    to_emails = [email.strip() for email in request.form.get('to', '').split(',') if email.strip()]
    cc_emails = [email.strip() for email in request.form.get('cc', '').split(',') if email.strip()]
    bcc_emails = [email.strip() for email in request.form.get('bcc', '').split(',') if email.strip()]
    
    new_message = {
        'to': to_emails,
        'cc': cc_emails,
        'bcc': bcc_emails,
        'subject': request.form.get('subject', ''),
        'body': request.form.get('body', '')
    }
    
    if 'messages' not in config:
        config['messages'] = []
    
    config['messages'].append(new_message)
    config['from_name'] = request.form.get('from_name', '')
    
    save_config(config)
    flash('Mensagem adicionada com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/delete_message/<int:message_id>')
def delete_message(message_id):
    """Remove uma mensagem"""
    config = load_config()
    
    if 0 <= message_id < len(config.get('messages', [])):
        del config['messages'][message_id]
        save_config(config)
        flash('Mensagem removida com sucesso!', 'success')
    else:
        flash('Mensagem não encontrada!', 'error')
    
    return redirect(url_for('index'))

@app.route('/send_emails')
def send_emails():
    """Envia todos os e-mails"""
    try:
        load_env_vars()
        sender_email = os.getenv('EMAIL_ADDRESS')
        app_password = os.getenv('EMAIL_APP_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD')
        
        
        if not sender_email or not app_password:
            flash('Configure EMAIL_ADDRESS e EMAIL_APP_PASSWORD no arquivo .env!', 'error')
            return redirect(url_for('index'))
        
        config = load_config()
        from_name = config.get('from_name', '')
        messages = config.get('messages', [])
        
        if not messages:
            flash('Nenhuma mensagem configurada!', 'error')
            return redirect(url_for('index'))
        
        sent_count = 0
        for idx, message_data in enumerate(messages, 1):
            try:
                msg = build_email_message(from_name, sender_email, message_data)
                send_via_gmail(msg, sender_email, app_password, dry_run=False)
                sent_count += 1
            except Exception as e:
                flash(f'Erro ao enviar mensagem {idx}: {str(e)}', 'error')
        
        if sent_count > 0:
            flash(f'{sent_count} e-mail(s) enviado(s) com sucesso!', 'success')
        
    except Exception as e:
        flash(f'Erro geral: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/preview/<int:message_id>')
def preview_message(message_id):
    """Visualiza uma mensagem"""
    config = load_config()
    
    if 0 <= message_id < len(config.get('messages', [])):
        message = config['messages'][message_id]
        from_name = config.get('from_name', '')
        
        # Simular construção da mensagem para preview
        try:
            load_env_vars()
            sender_email = os.getenv('EMAIL_ADDRESS') or 'seu.email@gmail.com'
            msg = build_email_message(from_name, sender_email, message)
            
            preview_data = {
                'from': msg['From'],
                'to': msg.get('To', ''),
                'cc': msg.get('Cc', ''),
                'subject': msg.get('Subject', ''),
                'body': msg.get_content(),
                'recipients': msg.__dict__.get('all_recipients', [])
            }
            
            return render_template('preview.html', preview=preview_data, message_id=message_id)
        except Exception as e:
            flash(f'Erro ao gerar preview: {str(e)}', 'error')
            return redirect(url_for('index'))
    else:
        flash('Mensagem não encontrada!', 'error')
        return redirect(url_for('index'))

@app.route('/send_single/<int:message_id>')
def send_single_email(message_id):
    """Envia um e-mail individual"""
    try:
        load_env_vars()
        sender_email = os.getenv('EMAIL_ADDRESS')
        app_password = os.getenv('EMAIL_APP_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD')
        
        
        if not sender_email or not app_password:
            flash('Configure EMAIL_ADDRESS e EMAIL_APP_PASSWORD no arquivo .env!', 'error')
            return redirect(url_for('index'))
        
        config = load_config()
        from_name = config.get('from_name', '')
        messages = config.get('messages', [])
        
        if 0 <= message_id < len(messages):
            message_data = messages[message_id]
            try:
                msg = build_email_message(from_name, sender_email, message_data)
                send_via_gmail(msg, sender_email, app_password, dry_run=False)
                flash(f'E-mail enviado com sucesso para {len(message_data.get("to", []))} destinatário(s)!', 'success')
            except Exception as e:
                flash(f'Erro ao enviar e-mail: {str(e)}', 'error')
        else:
            flash('Mensagem não encontrada!', 'error')
        
    except Exception as e:
        flash(f'Erro geral: {str(e)}', 'error')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
