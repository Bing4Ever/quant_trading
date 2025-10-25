"""
Strategy Service Layer

Business logic for strategy analysis and signal generation.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from api.models.strategy_models import (
    StrategyAnalysisRequest,
    BatchAnalysisRequest,
    StrategyAnalysisResponse,
    BatchAnalysisResponse,
    SignalResponse,
    SignalType
)


logger = logging.getLogger(__name__)


class StrategyService:
    """Service for strategy analysis operations."""
    
    def __init__(self):
        """Initialize strategy service."""
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def analyze_symbol(self, request: StrategyAnalysisRequest) -> StrategyAnalysisResponse:
        """Analyze a single symbol with specified strategies."""
        start_time = time.time()
        
        try:
            # Import here to avoid circular dependencies
            from src.tradingagent.modules.strategies import MovingAverageStrategy as MovingAverageCrossover
            from src.tradingagent.modules.strategies import RSIStrategy
            from src.tradingagent.modules import DataManager
            
            # Fetch data through Agent's DataProvider
            data_provider = DataManager()
            # Convert period to date range
            end_date = datetime.now().strftime("%Y-%m-%d")
            # Simple period conversion (could be improved)
            days_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
            days = days_map.get(request.period, 365)
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            df = data_provider.get_historical_data(
                symbol=request.symbol,
                start_date=start_date,
                end_date=end_date,
                interval=request.interval
            )
            
            if df is None or df.empty:
                return StrategyAnalysisResponse(
                    symbol=request.symbol,
                    strategy="all",
                    success=False,
                    error="Failed to fetch data",
                    analysis_time=datetime.now().isoformat()
                )
            
            # Run strategies based on request
            signals = []
            performance_metrics = {}
            
            if "all" in request.strategies or "ma_crossover" in request.strategies:
                ma_strategy = MovingAverageCrossover()
                signal = ma_strategy.generate_signals(df)
                if signal:
                    signals.append(signal)
                    performance_metrics['ma_crossover'] = self._calculate_metrics(df, signal)
            
            if "all" in request.strategies or "rsi" in request.strategies:
                rsi_strategy = RSIStrategy()
                signal = rsi_strategy.generate_signals(df)
                if signal:
                    signals.append(signal)
                    performance_metrics['rsi'] = self._calculate_metrics(df, signal)
            
            # Combine signals
            combined_signal = self._combine_signals(signals) if signals else None
            
            return StrategyAnalysisResponse(
                symbol=request.symbol,
                strategy=",".join(request.strategies),
                signal=combined_signal,
                performance_metrics=performance_metrics,
                analysis_time=datetime.now().isoformat(),
                success=True
            )
            
        except Exception as e:
            logger.error(f"Strategy analysis failed for {request.symbol}: {e}")
            return StrategyAnalysisResponse(
                symbol=request.symbol,
                strategy=",".join(request.strategies),
                success=False,
                error=str(e),
                analysis_time=datetime.now().isoformat()
            )
    
    def batch_analyze(self, request: BatchAnalysisRequest) -> BatchAnalysisResponse:
        """Analyze multiple symbols in parallel."""
        start_time = time.time()
        results = []
        
        # Create individual analysis requests
        analysis_requests = [
            StrategyAnalysisRequest(
                symbol=symbol,
                strategies=request.strategies,
                period=request.period,
                interval=request.interval
            )
            for symbol in request.symbols
        ]
        
        # Execute in parallel
        futures = {
            self.executor.submit(self.analyze_symbol, req): req.symbol 
            for req in analysis_requests
        }
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                symbol = futures[future]
                logger.error(f"Batch analysis failed for {symbol}: {e}")
                results.append(StrategyAnalysisResponse(
                    symbol=symbol,
                    strategy="all",
                    success=False,
                    error=str(e),
                    analysis_time=datetime.now().isoformat()
                ))
        
        # Calculate summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        buy_signals = sum(1 for r in results if r.signal and r.signal.signal_type == SignalType.BUY)
        sell_signals = sum(1 for r in results if r.signal and r.signal.signal_type == SignalType.SELL)
        
        summary = {
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "avg_confidence": sum(r.signal.confidence for r in results if r.signal) / len([r for r in results if r.signal]) if any(r.signal for r in results) else 0
        }
        
        execution_time = time.time() - start_time
        
        return BatchAnalysisResponse(
            results=results,
            total_analyzed=len(results),
            successful=successful,
            failed=failed,
            execution_time=execution_time,
            summary=summary
        )
    
    def _calculate_metrics(self, df, signal) -> Dict[str, Any]:
        """Calculate performance metrics for a strategy."""
        # Simplified metrics calculation
        return {
            "data_points": len(df),
            "signal_strength": signal.get('confidence', 0) if isinstance(signal, dict) else 0.5
        }
    
    def _combine_signals(self, signals: List[Any]) -> SignalResponse:
        """Combine multiple signals into a consensus signal."""
        if not signals:
            return None
        
        # Simple voting mechanism
        buy_votes = sum(1 for s in signals if s.get('action') == 'buy')
        sell_votes = sum(1 for s in signals if s.get('action') == 'sell')
        
        if buy_votes > sell_votes:
            signal_type = SignalType.BUY
            confidence = buy_votes / len(signals)
        elif sell_votes > buy_votes:
            signal_type = SignalType.SELL
            confidence = sell_votes / len(signals)
        else:
            signal_type = SignalType.HOLD
            confidence = 0.5
        
        # Get first signal as template
        first_signal = signals[0]
        
        return SignalResponse(
            symbol=first_signal.get('symbol', 'UNKNOWN'),
            signal_type=signal_type,
            strategy="combined",
            confidence=confidence,
            price=first_signal.get('price', 0),
            timestamp=datetime.now().isoformat(),
            indicators={},
            reason=f"Combined {len(signals)} signals: {buy_votes} buy, {sell_votes} sell"
        )
