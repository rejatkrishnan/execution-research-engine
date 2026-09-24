# Execution Research Engine

A research codebase for studying market microstructure, transaction costs, and algorithmic execution.

The project is growing incrementally from a deterministic limit order book into a small execution research stack with matching, market-data replay, TWAP/VWAP/POV strategies, slippage and impact models, transaction-cost analysis, and benchmarking.

## Current capabilities

- typed limit and market orders
- price-time-priority matching with partial fills
- best bid, best ask, spread, and price-level depth
- order cancellation and input validation
- fill events and multi-level market-order sweeps
- execution VWAP and signed slippage analytics
- implementation shortfall decomposition into execution and opportunity cost

## Development

~~~bash
python -m pip install -e '.[dev]'
pytest
~~~

## Roadmap

1. Price-time-priority matching and partial fills
2. Trade and fill event model
3. Synthetic and historical market-data replay
4. TWAP, VWAP, and POV execution strategies
5. Slippage, implementation shortfall, and market-impact analytics
6. Queue-position modeling and execution benchmarks
7. Performance profiling and selected C++ acceleration
