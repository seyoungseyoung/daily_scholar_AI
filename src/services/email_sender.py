import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict, Any

class EmailSender:
    def __init__(self):
        load_dotenv()  # .env 파일 로드
        
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('SMTP_USERNAME')
        self.sender_password = os.getenv('SMTP_PASSWORD')
        self.subject_prefix = os.getenv('EMAIL_SUBJECT_PREFIX', '[DailyAI Scholar] ')
        
        # Load recipient list
        self.recipient_list = self._load_recipient_list()
    
    def _load_recipient_list(self) -> List[str]:
        """Load recipient email addresses from config file."""
        # 프로젝트 루트 디렉토리 찾기
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        email_file = os.path.join(current_dir, "config", "email_list.txt")
        
        if not os.path.exists(email_file):
            print(f"Warning: {email_file} not found. No emails will be sent.")
            return []
        
        try:
            with open(email_file, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except UnicodeDecodeError:
            # UTF-8로 읽기 실패 시 다른 인코딩 시도
            try:
                with open(email_file, 'r', encoding='cp949') as f:
                    return [line.strip() for line in f if line.strip() and not line.startswith('#')]
            except Exception as e:
                print(f"Error reading email list: {str(e)}")
                return []
    
    def _create_html_content(self, papers: List[Dict[str, Any]]) -> str:
        """Create HTML content for the email."""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .paper {{ margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .title {{ font-size: 1.2em; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
                .tags {{ margin: 10px 0; }}
                .tag {{ display: inline-block; background: #e1f5fe; padding: 3px 8px; border-radius: 12px; margin: 2px; font-size: 0.9em; }}
                .summary {{ margin: 10px 0; }}
                .translation {{ margin: 10px 0; padding: 10px; background: #f5f5f5; }}
                .meta {{ font-size: 0.9em; color: #666; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <h1>Daily AI Paper Report</h1>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        for paper in papers:
            html += f"""
            <div class="paper">
                <div class="title">{paper['title']}</div>
                <div class="tags">
                    {''.join([f'<span class="tag">{tag}</span>' for tag in paper.get('tags', [])])}
                </div>
                <div class="summary">
                    <h3>Summary</h3>
                    {paper.get('summary', '')}
                </div>
                <div class="translation">
                    <h3>Korean Translation</h3>
                    {paper.get('translation', '')}
                </div>
                <div class="meta">
                    <p>Publication Date: {paper.get('submission_date', '')}</p>
                    <p><a href="{paper.get('html_url', '#')}" target="_blank">View Paper</a></p>
                </div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        return html
    
    def send_report(self, papers: List[Dict[str, Any]]) -> bool:
        """Send the paper report to all recipients."""
        if not self.recipient_list:
            print("No recipients found. Skipping email sending.")
            return False
        
        if not all([self.sender_email, self.sender_password]):
            print("Sender credentials not configured. Skipping email sending.")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"{self.subject_prefix}Daily AI Paper Report - {datetime.now().strftime('%Y-%m-%d')}"
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(self.recipient_list)
            
            html_content = self._create_html_content(papers)
            msg.attach(MIMEText(html_content, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f"Report sent successfully to {len(self.recipient_list)} recipients")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False 