#!/usr/bin/env python3
"""
通知管理器模块
支持多种通知方式：邮件、微信、钉钉等
"""

import smtplib
import requests
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import os
from datetime import datetime

@dataclass
class NotificationConfig:
    """通知配置数据类"""
    email_enabled: bool = False
    email_smtp_server: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: List[str] = None
    
    wechat_enabled: bool = False
    wechat_webhook_url: str = ""
    
    dingtalk_enabled: bool = False
    dingtalk_webhook_url: str = ""
    dingtalk_secret: str = ""

class NotificationManager:
    """通知管理器"""
    
    def __init__(self, config_file: str = "config/notification_config.json"):
        """
        初始化通知管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.logger = logging.getLogger("NotificationManager")
        self.config = self.load_config()
    
    def load_config(self) -> NotificationConfig:
        """加载通知配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                return NotificationConfig(**config_data)
            else:
                # 创建默认配置
                default_config = NotificationConfig()
                self.save_config(default_config)
                return default_config
        except Exception as e:
            self.logger.error(f"加载通知配置失败: {str(e)}")
            return NotificationConfig()
    
    def save_config(self, config: NotificationConfig):
        """保存通知配置"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            config_data = {
                "email_enabled": config.email_enabled,
                "email_smtp_server": config.email_smtp_server,
                "email_smtp_port": config.email_smtp_port,
                "email_username": config.email_username,
                "email_password": config.email_password,
                "email_recipients": config.email_recipients or [],
                "wechat_enabled": config.wechat_enabled,
                "wechat_webhook_url": config.wechat_webhook_url,
                "dingtalk_enabled": config.dingtalk_enabled,
                "dingtalk_webhook_url": config.dingtalk_webhook_url,
                "dingtalk_secret": config.dingtalk_secret
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"保存通知配置失败: {str(e)}")
    
    def send_email(self, subject: str, content: str, attachments: List[str] = None) -> bool:
        """
        发送邮件通知
        
        Args:
            subject: 邮件主题
            content: 邮件内容
            attachments: 附件文件路径列表
            
        Returns:
            是否发送成功
        """
        if not self.config.email_enabled:
            return False
            
        try:
            # 创建邮件消息
            msg = MIMEMultipart()
            msg['From'] = self.config.email_username
            msg['To'] = ", ".join(self.config.email_recipients)
            msg['Subject'] = subject
            
            # 添加邮件正文
            msg.attach(MIMEText(content, 'html', 'utf-8'))
            
            # 添加附件
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(file_path)}'
                        )
                        msg.attach(part)
            
            # 发送邮件
            server = smtplib.SMTP(self.config.email_smtp_server, self.config.email_smtp_port)
            server.starttls()
            server.login(self.config.email_username, self.config.email_password)
            
            text = msg.as_string()
            server.sendmail(self.config.email_username, self.config.email_recipients, text)
            server.quit()
            
            self.logger.info(f"邮件发送成功: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"邮件发送失败: {str(e)}")
            return False
    
    def send_wechat_message(self, content: str) -> bool:
        """
        发送微信机器人消息
        
        Args:
            content: 消息内容
            
        Returns:
            是否发送成功
        """
        if not self.config.wechat_enabled:
            return False
            
        try:
            data = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
            
            response = requests.post(
                self.config.wechat_webhook_url,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("微信消息发送成功")
                return True
            else:
                self.logger.error(f"微信消息发送失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"微信消息发送失败: {str(e)}")
            return False
    
    def send_dingtalk_message(self, content: str, title: str = "量化交易通知") -> bool:
        """
        发送钉钉机器人消息
        
        Args:
            content: 消息内容
            title: 消息标题
            
        Returns:
            是否发送成功
        """
        if not self.config.dingtalk_enabled:
            return False
            
        try:
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": content
                }
            }
            
            response = requests.post(
                self.config.dingtalk_webhook_url,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    self.logger.info("钉钉消息发送成功")
                    return True
                else:
                    self.logger.error(f"钉钉消息发送失败: {result}")
                    return False
            else:
                self.logger.error(f"钉钉消息发送失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"钉钉消息发送失败: {str(e)}")
            return False
    
    def send_notification(self, title: str, content: str, attachments: List[str] = None):
        """
        发送多渠道通知
        
        Args:
            title: 通知标题
            content: 通知内容
            attachments: 附件列表
        """
        # 发送邮件
        if self.config.email_enabled:
            email_content = self._format_email_content(title, content)
            self.send_email(title, email_content, attachments)
        
        # 发送微信消息
        if self.config.wechat_enabled:
            wechat_content = f"{title}\n\n{content}"
            self.send_wechat_message(wechat_content)
        
        # 发送钉钉消息
        if self.config.dingtalk_enabled:
            dingtalk_content = self._format_dingtalk_content(title, content)
            self.send_dingtalk_message(dingtalk_content, title)
    
    def _format_email_content(self, title: str, content: str) -> str:
        """格式化邮件内容为HTML"""
        # 处理换行符
        formatted_content = content.replace('\n', '<br>')
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        html_content = f"""
        <html>
        <head></head>
        <body>
            <h2 style="color: #2E86AB;">{title}</h2>
            <div style="font-family: Arial, sans-serif; line-height: 1.6;">
                {formatted_content}
            </div>
            <hr>
            <p style="color: #666; font-size: 12px;">
                发送时间: {current_time}
            </p>
        </body>
        </html>
        """
        return html_content
    
    def _format_dingtalk_content(self, title: str, content: str) -> str:
        """格式化钉钉内容为Markdown"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        markdown_content = f"""
# {title}

{content}

---
🕐 **发送时间**: {current_time}
        """
        return markdown_content
    
    def send_task_completion_notification(self, task_name: str, 
                                        results_summary: Dict[str, Any],
                                        report_file: str = ""):
        """
        发送任务完成通知
        
        Args:
            task_name: 任务名称
            results_summary: 结果摘要
            report_file: 报告文件路径
        """
        title = f"✅ 任务完成通知: {task_name}"
        
        content = f"""
任务 "{task_name}" 已成功完成！

📊 **执行摘要**:
- 分析股票数量: {results_summary.get('analyzed_symbols', 0)}
- 成功分析数量: {results_summary.get('successful_analysis', 0)}

🏆 **最佳策略表现**:
"""
        
        best_strategies = results_summary.get('best_strategies', {})
        for symbol, strategy_info in best_strategies.items():
            content += f"""
- **{symbol}**: {strategy_info.get('strategy', 'N/A')}
  - 收益率: {strategy_info.get('return', 0):.2%}
  - 夏普比率: {strategy_info.get('sharpe', 0):.3f}
"""
        
        # 添加附件
        attachments = [report_file] if report_file and os.path.exists(report_file) else None
        
        self.send_notification(title, content, attachments)
    
    def send_error_notification(self, task_name: str, error_message: str):
        """
        发送错误通知
        
        Args:
            task_name: 任务名称
            error_message: 错误消息
        """
        title = f"❌ 任务执行失败: {task_name}"
        
        content = f"""
任务 "{task_name}" 执行失败！

🚨 **错误信息**:
{error_message}

⏰ **失败时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

请检查系统日志获取详细信息。
"""
        
        self.send_notification(title, content)
    
    def send_trading_signal_notification(self, symbol: str, strategy: str, 
                                       signal: str, price: float, reason: str = ""):
        """
        发送交易信号通知
        
        Args:
            symbol: 股票代码
            strategy: 策略名称
            signal: 信号类型
            price: 当前价格
            reason: 信号原因
        """
        signal_emoji = "📈" if signal.upper() == "BUY" else "📉" if signal.upper() == "SELL" else "⏸️"
        
        title = f"{signal_emoji} 交易信号: {symbol}"
        
        content = f"""
检测到新的交易信号！

📊 **信号详情**:
- 股票代码: **{symbol}**
- 策略名称: **{strategy}**
- 信号类型: **{signal}**
- 当前价格: **${price:.2f}**
- 信号原因: {reason}

⏰ **信号时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        self.send_notification(title, content)

# 使用示例
if __name__ == "__main__":
    # 创建通知管理器
    notification_manager = NotificationManager()
    
    # 发送测试通知
    notification_manager.send_notification(
        title="系统测试通知",
        content="这是一条测试消息，用于验证通知系统是否正常工作。"
    )