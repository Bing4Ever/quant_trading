"""数据持久化系统 - 回测结果数据库管理和数据分析工具。"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

class BacktestDatabase:
    """回测结果数据库管理"""

    def __init__(self, db_path="db/backtest_results.db"):
        self.db_path = Path(db_path)
        # Create db directory if it doesn't exist
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()

        # 配置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 创建回测结果表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backtest_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    strategy_params TEXT NOT NULL,
                    backtest_config TEXT,
                    total_return REAL,
                    annualized_return REAL,
                    sharpe_ratio REAL,
                    max_drawdown REAL,
                    volatility REAL,
                    win_rate REAL,
                    total_trades INTEGER,
                    avg_trade_return REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
            ''')

            # 创建收藏列表表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorite_stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT UNIQUE NOT NULL,
                    name TEXT,
                    sector TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_backtest_id INTEGER,
                    notes TEXT,
                    FOREIGN KEY (last_backtest_id) REFERENCES backtest_results (id)
                )
            ''')

            # 创建参数优化记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimization_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    parameter_name TEXT NOT NULL,
                    parameter_value TEXT NOT NULL,
                    performance_metric REAL,
                    metric_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 创建策略比较表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_comparison (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    comparison_name TEXT NOT NULL,
                    symbols TEXT NOT NULL,
                    results TEXT NOT NULL,
                    best_performer TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

    def save_backtest_result(self, *, symbol, strategy_name, strategy_params, results,
                           backtest_config=None, notes=""):
        """保存回测结果

        Args:
            symbol: 股票代码
            strategy_name: 策略名称
            strategy_params: 策略参数
            results: 回测结果
            backtest_config: 回测配置参数 (新增)
            notes: 备注
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 如果没有提供回测配置，创建默认配置
                if backtest_config is None:
                    backtest_config = {
                        'start_date': None,
                        'end_date': None,
                        'initial_capital': 100000,
                        'commission': 0.001,
                        'slippage': 0.0005,
                        'data_source': 'yfinance',
                        'backtest_mode': 'full',
                        'optimization_used': False
                    }

                cursor.execute('''
                    INSERT INTO backtest_results (
                        symbol, strategy_name, strategy_params, backtest_config,
                        total_return, annualized_return, sharpe_ratio,
                        max_drawdown, volatility, win_rate,
                        total_trades, avg_trade_return, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    strategy_name,
                    json.dumps(strategy_params, ensure_ascii=False),
                    json.dumps(backtest_config, ensure_ascii=False),
                    results.get('total_return', 0),
                    results.get('annualized_return', 0),
                    results.get('sharpe_ratio', 0),
                    results.get('max_drawdown', 0),
                    results.get('volatility', 0),
                    results.get('win_rate', 0),
                    results.get('total_trades', 0),
                    results.get('avg_trade_return', 0),
                    notes
                ))

                result_id = cursor.lastrowid
                conn.commit()

                # 如果是收藏的股票，更新最新回测ID
                if self.is_favorite(symbol):
                    self.update_favorite_backtest(symbol, result_id)

                self.logger.info(f"回测结果已保存，ID: {result_id}")
                return result_id

        except Exception as e:
            self.logger.error(f"保存回测结果失败: {str(e)}")
            return None

    def get_backtest_history(self, symbol=None, limit=50):
        """获取回测历史记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if symbol:
                    query = '''
                        SELECT * FROM backtest_results
                        WHERE symbol = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    '''
                    df = pd.read_sql_query(query, conn, params=(symbol, limit))
                else:
                    query = '''
                        SELECT * FROM backtest_results
                        ORDER BY created_at DESC
                        LIMIT ?
                    '''
                    df = pd.read_sql_query(query, conn, params=(limit,))

                # 解析策略参数和回测配置
                if not df.empty:
                    df['strategy_params'] = df['strategy_params'].apply(
                        lambda x: json.loads(x) if x else {}
                    )
                    df['backtest_config'] = df['backtest_config'].apply(
                        lambda x: json.loads(x) if x else {}
                    )

                return df

        except Exception as e:
            self.logger.error(f"获取历史记录失败: {str(e)}")
            return pd.DataFrame()

    def get_all_results(self, limit=None):
        """获取所有回测结果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if limit:
                    query = '''
                        SELECT * FROM backtest_results
                        ORDER BY created_at DESC
                        LIMIT ?
                    '''
                    df = pd.read_sql_query(query, conn, params=(limit,))
                else:
                    query = '''
                        SELECT * FROM backtest_results
                        ORDER BY created_at DESC
                    '''
                    df = pd.read_sql_query(query, conn)

                # 解析JSON参数
                if not df.empty and 'strategy_params' in df.columns:
                    df['strategy_params'] = df['strategy_params'].apply(json.loads)
                    if 'backtest_config' in df.columns:
                        df['backtest_config'] = df['backtest_config'].apply(json.loads)

                return df

        except Exception as e:
            self.logger.error(f"获取所有回测结果失败: {str(e)}")
            return pd.DataFrame()

    def save_optimization_result(self, *, symbol, parameter_name, parameter_value,
                               performance_metric, metric_type):
        """保存参数优化结果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO optimization_history (
                        symbol, parameter_name, parameter_value,
                        performance_metric, metric_type
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    parameter_name,
                    str(parameter_value),
                    performance_metric,
                    metric_type
                ))

                conn.commit()

        except Exception as e:
            self.logger.error(f"保存优化结果失败: {str(e)}")

    def get_optimization_history(self, symbol, parameter_name=None):
        """获取参数优化历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if parameter_name:
                    query = '''
                        SELECT * FROM optimization_history
                        WHERE symbol = ? AND parameter_name = ?
                        ORDER BY created_at DESC
                    '''
                    df = pd.read_sql_query(query, conn, params=(symbol, parameter_name))
                else:
                    query = '''
                        SELECT * FROM optimization_history
                        WHERE symbol = ?
                        ORDER BY created_at DESC
                    '''
                    df = pd.read_sql_query(query, conn, params=(symbol,))

                return df

        except Exception as e:
            self.logger.error(f"获取优化历史失败: {str(e)}")
            return pd.DataFrame()

    def add_favorite_stock(self, symbol, name=None, sector=None, notes=None):
        """添加股票到收藏列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT OR REPLACE INTO favorite_stocks (
                        symbol, name, sector, notes, added_at
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    symbol.upper(),
                    name,
                    sector,
                    notes,
                    datetime.now()
                ))

                conn.commit()
                self.logger.info(f"已将 {symbol} 添加到收藏列表")
                return True

        except Exception as e:
            self.logger.error(f"添加收藏股票失败: {str(e)}")
            return False

    def remove_favorite_stock(self, symbol):
        """从收藏列表移除股票"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('DELETE FROM favorite_stocks WHERE symbol = ?', (symbol.upper(),))

                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"已从收藏列表移除 {symbol}")
                    return True
                return False

        except Exception as e:
            self.logger.error(f"移除收藏股票失败: {str(e)}")
            return False

    def get_favorite_stocks(self):
        """获取收藏的股票列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT f.*,
                           b.total_return as last_return,
                           b.sharpe_ratio as last_sharpe,
                           b.created_at as last_backtest_date
                    FROM favorite_stocks f
                    LEFT JOIN backtest_results b ON f.last_backtest_id = b.id
                    ORDER BY f.added_at DESC
                '''
                df = pd.read_sql_query(query, conn)
                return df

        except Exception as e:
            self.logger.error(f"获取收藏列表失败: {str(e)}")
            return pd.DataFrame()

    def update_favorite_backtest(self, symbol, result_id):
        """更新收藏股票的最新回测ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    UPDATE favorite_stocks
                    SET last_backtest_id = ?
                    WHERE symbol = ?
                ''', (result_id, symbol.upper()))

                conn.commit()

        except Exception as e:
            self.logger.error(f"更新收藏股票回测ID失败: {str(e)}")

    def is_favorite(self, symbol):
        """检查股票是否在收藏列表中"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT COUNT(*) FROM favorite_stocks WHERE symbol = ?', (symbol.upper(),))
                count = cursor.fetchone()[0]

                return count > 0

        except Exception as e:
            self.logger.error(f"检查收藏状态失败: {str(e)}")
            return False

    def save_comparison_result(self, comparison_name, symbols, results, best_performer):
        """保存策略比较结果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO strategy_comparison (
                        comparison_name, symbols, results, best_performer
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    comparison_name,
                    json.dumps(symbols),
                    json.dumps(results),
                    best_performer
                ))

                conn.commit()

        except Exception as e:
            self.logger.error(f"保存比较结果失败: {str(e)}")

    def get_comparison_history(self, limit=20):
        """获取比较分析历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT * FROM strategy_comparison
                    ORDER BY created_at DESC
                    LIMIT ?
                '''
                df = pd.read_sql_query(query, conn, params=(limit,))

                if not df.empty:
                    df['symbols'] = df['symbols'].apply(json.loads)
                    df['results'] = df['results'].apply(json.loads)

                return df

        except Exception as e:
            self.logger.error(f"获取比较历史失败: {str(e)}")
            return pd.DataFrame()

    def get_performance_trends(self, symbol, days=30):
        """获取性能趋势数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = f'''
                    SELECT
                        DATE(created_at) as date,
                        AVG(total_return) as avg_return,
                        AVG(sharpe_ratio) as avg_sharpe,
                        AVG(max_drawdown) as avg_drawdown,
                        COUNT(*) as test_count
                    FROM backtest_results
                    WHERE symbol = ? AND created_at >= date('now', '-{days} days')
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                '''

                df = pd.read_sql_query(query, conn, params=(symbol,))
                return df

        except Exception as e:
            self.logger.error(f"获取趋势数据失败: {str(e)}")
            return pd.DataFrame()

    def get_best_parameters(self, symbol, metric='total_return', limit=10):
        """获取最佳参数组合"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = f'''
                    SELECT
                        strategy_params,
                        backtest_config,
                        {metric},
                        total_return,
                        sharpe_ratio,
                        max_drawdown,
                        created_at
                    FROM backtest_results
                    WHERE symbol = ?
                    ORDER BY {metric} DESC
                    LIMIT ?
                '''

                df = pd.read_sql_query(query, conn, params=(symbol, limit))

                if not df.empty:
                    df['strategy_params'] = df['strategy_params'].apply(
                        lambda x: json.loads(x) if x else {}
                    )
                    if 'backtest_config' in df.columns:
                        df['backtest_config'] = df['backtest_config'].apply(
                            lambda x: json.loads(x) if x else {}
                        )

                return df

        except Exception as e:
            self.logger.error(f"获取最佳参数失败: {str(e)}")
            return pd.DataFrame()

    def get_statistics(self):
        """获取数据库统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                db_stats = {}

                # 回测总数
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM backtest_results")
                db_stats['total_backtests'] = cursor.fetchone()[0]

                # 不同股票数量
                cursor.execute("SELECT COUNT(DISTINCT symbol) FROM backtest_results")
                db_stats['unique_symbols'] = cursor.fetchone()[0]

                # 最近测试时间
                cursor.execute("SELECT MAX(created_at) FROM backtest_results")
                db_stats['latest_test'] = cursor.fetchone()[0]

                # 平均表现
                cursor.execute('''
                    SELECT
                        AVG(total_return) as avg_return,
                        AVG(sharpe_ratio) as avg_sharpe,
                        AVG(max_drawdown) as avg_drawdown
                    FROM backtest_results
                ''')
                avg_stats = cursor.fetchone()
                db_stats['avg_return'] = avg_stats[0] if avg_stats[0] else 0
                db_stats['avg_sharpe'] = avg_stats[1] if avg_stats[1] else 0
                db_stats['avg_drawdown'] = avg_stats[2] if avg_stats[2] else 0

                return db_stats

        except Exception as e:
            self.logger.error(f"获取统计信息失败: {str(e)}")
            return {}

    def export_data(self, output_path="backtest_export.csv"):
        """导出数据到CSV"""
        try:
            df = self.get_backtest_history(limit=1000)
            df.to_csv(output_path, index=False, encoding='utf-8')
            self.logger.info(f"数据已导出到: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"数据导出失败: {str(e)}")
            return None

    def cleanup_old_data(self, days=90):
        """清理旧数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 删除超过指定天数的记录
                cursor.execute(f'''
                    DELETE FROM backtest_results
                    WHERE created_at < date('now', '-{days} days')
                ''')

                cursor.execute(f'''
                    DELETE FROM optimization_history
                    WHERE created_at < date('now', '-{days} days')
                ''')

                deleted_count = cursor.rowcount
                conn.commit()

                self.logger.info(f"已清理 {deleted_count} 条旧记录")
                return deleted_count

        except Exception as e:
            self.logger.error(f"清理数据失败: {str(e)}")
            return 0

    def _convert_result_row(self, row_dict):
        """Convert database row to formatted result dictionary."""
        # Parse JSON fields
        json_fields = ['strategy_params', 'backtest_config']
        for field in json_fields:
            if row_dict.get(field):
                try:
                    row_dict[field] = json.loads(row_dict[field])
                except json.JSONDecodeError:
                    pass
        return row_dict

    def get_backtest_results(self, *, start_date=None, end_date=None,
                           strategy_name=None, symbol=None, limit=None):
        """获取回测结果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # 允许按列名访问
                cursor = conn.cursor()

                # 构建查询条件
                where_conditions = []
                params = []

                if start_date:
                    where_conditions.append("created_at >= ?")
                    params.append(start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date))

                if end_date:
                    where_conditions.append("created_at <= ?")
                    params.append(end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date))

                if strategy_name:
                    where_conditions.append("strategy_name = ?")
                    params.append(strategy_name)

                if symbol:
                    where_conditions.append("symbol = ?")
                    params.append(symbol)

                # 构建完整查询
                query = "SELECT * FROM backtest_results"
                if where_conditions:
                    query += " WHERE " + " AND ".join(where_conditions)
                query += " ORDER BY created_at DESC"

                if limit:
                    query += f" LIMIT {limit}"

                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [self._convert_result_row(dict(row)) for row in rows]

        except Exception as e:
            self.logger.error(f"获取回测结果失败: {str(e)}")
            return []

# 数据分析工具
class BacktestAnalytics:
    """回测数据分析工具"""

    def __init__(self, db_path="db/backtest_results.db"):
        self.db = BacktestDatabase(db_path)

    def analyze_parameter_sensitivity(self, symbol, parameter_name):
        """分析参数敏感性"""
        df = self.db.get_optimization_history(symbol, parameter_name)

        if df.empty:
            return None

        # 按参数值分组分析
        analysis = df.groupby('parameter_value').agg({
            'performance_metric': ['mean', 'std', 'count'],
            'created_at': 'max'
        }).round(4)

        return analysis

    def generate_performance_report(self, symbol):
        """生成性能分析报告"""
        history = self.db.get_backtest_history(symbol, limit=100)

        if history.empty:
            return "无历史数据"

        # 计算统计指标
        performance_stats = {
            'total_tests': len(history),
            'avg_return': history['total_return'].mean(),
            'best_return': history['total_return'].max(),
            'worst_return': history['total_return'].min(),
            'avg_sharpe': history['sharpe_ratio'].mean(),
            'stability': history['total_return'].std(),
            'success_rate': (history['total_return'] > 0).mean()
        }

        report = f"""
        📊 {symbol} 性能分析报告

        🔢 测试次数: {performance_stats['total_tests']}
        📈 平均收益: {performance_stats['avg_return']:.2%}
        🏆 最佳收益: {performance_stats['best_return']:.2%}
        📉 最差收益: {performance_stats['worst_return']:.2%}
        📊 平均夏普: {performance_stats['avg_sharpe']:.3f}
        📏 收益稳定性: {performance_stats['stability']:.4f}
        ✅ 成功率: {performance_stats['success_rate']:.1%}
        """

        return report

if __name__ == "__main__":
    # 测试代码
    db = BacktestDatabase()

    # 测试保存数据
    test_results = {
        'total_return': 0.12,
        'sharpe_ratio': 1.5,
        'max_drawdown': -0.08,
        'win_rate': 0.6,
        'total_trades': 15
    }

    test_params = {
        'bb_period': 20,
        'rsi_period': 14,
        'rsi_oversold': 30,
        'rsi_overbought': 70
    }

    # 保存测试数据
    backtest_id = db.save_backtest_result(
        symbol="AAPL",
        strategy_name="MeanReversion",
        strategy_params=test_params,
        results=test_results,
        notes="测试数据"
    )

    print(f"测试数据已保存，ID: {backtest_id}")

    # 获取统计信息
    stats = db.get_statistics()
    print("数据库统计:", stats)
