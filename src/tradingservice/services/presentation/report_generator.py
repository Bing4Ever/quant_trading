# 📊 回测报告生成器
import os
import json
from datetime import datetime
from pathlib import Path

class BacktestReportGenerator:
    """专业的回测报告生成器"""
    
    def __init__(self, output_dir="reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_markdown_report(self, results, symbol, strategy_params=None):
        """生成Markdown格式报告"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# 📊 量化交易回测报告

## 基本信息
- **股票代码**: {symbol}
- **生成时间**: {timestamp}
- **策略类型**: 均值回归策略

## 📈 核心性能指标

| 指标 | 数值 | 评级 |
|------|------|------|
| 总收益率 | {results.get('total_return', 0):.2%} | {self._get_return_grade(results.get('total_return', 0))} |
| 年化收益率 | {results.get('annualized_return', 0):.2%} | {self._get_return_grade(results.get('annualized_return', 0))} |
| 夏普比率 | {results.get('sharpe_ratio', 0):.3f} | {self._get_sharpe_grade(results.get('sharpe_ratio', 0))} |
| 最大回撤 | {results.get('max_drawdown', 0):.2%} | {self._get_drawdown_grade(results.get('max_drawdown', 0))} |
| 胜率 | {results.get('win_rate', 0):.1%} | {self._get_winrate_grade(results.get('win_rate', 0))} |
| 波动率 | {results.get('volatility', 0):.2%} | - |
| 交易次数 | {results.get('total_trades', 0)} | - |

## 🎯 分析结论

### 策略表现
{self._generate_performance_summary(results)}

### 风险评估
{self._generate_risk_assessment(results)}

### 改进建议
{self._generate_improvement_suggestions(results)}

---
*报告由量化交易系统自动生成于 {timestamp}*
"""
        return report
    
    def generate_html_report(self, results, symbol, strategy_params=None):
        """生成HTML格式报告"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>量化交易回测报告 - {symbol}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #333; margin-bottom: 30px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .metric-label {{ color: #666; margin-top: 10px; }}
        .grade-good {{ color: #28a745; }}
        .grade-average {{ color: #ffc107; }}
        .grade-poor {{ color: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
        th {{ background: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 量化交易回测报告</h1>
            <h2>{symbol} - {timestamp}</h2>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value {self._get_css_class(results.get('total_return', 0), 'return')}">{results.get('total_return', 0):.2%}</div>
                <div class="metric-label">总收益率</div>
            </div>
            <div class="metric">
                <div class="metric-value {self._get_css_class(results.get('sharpe_ratio', 0), 'sharpe')}">{results.get('sharpe_ratio', 0):.3f}</div>
                <div class="metric-label">夏普比率</div>
            </div>
            <div class="metric">
                <div class="metric-value {self._get_css_class(results.get('max_drawdown', 0), 'drawdown')}">{results.get('max_drawdown', 0):.2%}</div>
                <div class="metric-label">最大回撤</div>
            </div>
            <div class="metric">
                <div class="metric-value {self._get_css_class(results.get('win_rate', 0), 'winrate')}">{results.get('win_rate', 0):.1%}</div>
                <div class="metric-label">胜率</div>
            </div>
        </div>
        
        <h3>📈 详细分析</h3>
        <p><strong>策略表现:</strong> {self._generate_performance_summary(results)}</p>
        <p><strong>风险评估:</strong> {self._generate_risk_assessment(results)}</p>
        <p><strong>改进建议:</strong> {self._generate_improvement_suggestions(results)}</p>
    </div>
</body>
</html>"""
        return html
    
    def _get_return_grade(self, value):
        if value > 0.15: return "🟢 优秀"
        elif value > 0.08: return "🟡 良好"
        elif value > 0: return "🟠 一般"
        else: return "🔴 不佳"
    
    def _get_sharpe_grade(self, value):
        if value > 2: return "🟢 优秀"
        elif value > 1: return "🟡 良好"
        elif value > 0: return "🟠 一般"
        else: return "🔴 不佳"
    
    def _get_drawdown_grade(self, value):
        value = abs(value)
        if value < 0.05: return "🟢 优秀"
        elif value < 0.1: return "🟡 良好"
        elif value < 0.2: return "🟠 一般"
        else: return "🔴 不佳"
    
    def _get_winrate_grade(self, value):
        if value > 0.6: return "🟢 优秀"
        elif value > 0.5: return "🟡 良好"
        elif value > 0.4: return "🟠 一般"
        else: return "🔴 不佳"
    
    def _get_css_class(self, value, metric_type):
        if metric_type == 'return':
            return 'grade-good' if value > 0.08 else 'grade-average' if value > 0 else 'grade-poor'
        elif metric_type == 'sharpe':
            return 'grade-good' if value > 1 else 'grade-average' if value > 0 else 'grade-poor'
        elif metric_type == 'drawdown':
            return 'grade-good' if abs(value) < 0.1 else 'grade-average' if abs(value) < 0.2 else 'grade-poor'
        elif metric_type == 'winrate':
            return 'grade-good' if value > 0.5 else 'grade-average' if value > 0.4 else 'grade-poor'
        return ''
    
    def _generate_performance_summary(self, results):
        total_return = results.get('total_return', 0)
        sharpe = results.get('sharpe_ratio', 0)
        
        if total_return > 0.1 and sharpe > 1:
            return "📈 策略表现优秀，收益和风险调整表现均超出预期"
        elif total_return > 0 and sharpe > 0:
            return "📊 策略表现中等，有盈利但仍有优化空间"
        else:
            return "📉 策略需要改进，当前参数下表现不佳"
    
    def _generate_risk_assessment(self, results):
        max_dd = abs(results.get('max_drawdown', 0))
        sharpe = results.get('sharpe_ratio', 0)
        
        if max_dd < 0.05 and sharpe > 1:
            return "✅ 低风险策略，回撤控制良好"
        elif max_dd < 0.1 and sharpe > 0.5:
            return "🟡 中等风险策略，风险水平可接受"
        else:
            return "🔴 高风险策略，需要加强风险管理"
    
    def _generate_improvement_suggestions(self, results):
        suggestions = []
        
        if results.get('total_return', 0) < 0:
            suggestions.append("考虑调整策略参数或更换股票")
        
        if results.get('sharpe_ratio', 0) < 0.5:
            suggestions.append("优化风险管理机制")
        
        if abs(results.get('max_drawdown', 0)) > 0.15:
            suggestions.append("设置更严格的止损")
        
        if results.get('win_rate', 0) < 0.4:
            suggestions.append("调整交易信号参数")
        
        if not suggestions:
            suggestions.append("当前策略表现良好")
        
        return "; ".join(suggestions)
    
    def save_report(self, content, filename, format_type="markdown"):
        """保存报告到文件"""
        ext = ".md" if format_type == "markdown" else ".html"
        filepath = self.output_dir / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(filepath)
    
    def generate_and_save_report(self, results, symbol, format_type="both"):
        """生成并保存报告"""
        reports = {}
        
        if format_type in ["markdown", "both"]:
            md_content = self.generate_markdown_report(results, symbol)
            md_path = self.save_report(md_content, f"{symbol}_report", "markdown")
            reports['markdown'] = md_path
        
        if format_type in ["html", "both"]:
            html_content = self.generate_html_report(results, symbol)
            html_path = self.save_report(html_content, f"{symbol}_report", "html")
            reports['html'] = html_path
        
        return reports

if __name__ == "__main__":
    # 测试代码
    test_results = {
        'total_return': 0.12,
        'sharpe_ratio': 1.5,
        'max_drawdown': -0.08,
        'win_rate': 0.6,
        'total_trades': 15
    }
    
    generator = BacktestReportGenerator()
    reports = generator.generate_and_save_report(test_results, "AAPL", "both")
    print("报告已生成:", reports)