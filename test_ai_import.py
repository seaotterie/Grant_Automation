#!/usr/bin/env python3
import sys
sys.path.append('.')

try:
    from src.processors.analysis.ai_lite_scorer import AILiteScorer
    print('AI-Lite scorer imported successfully')
    processor = AILiteScorer()
    print(f'Model: {processor.model}')
    print(f'Batch size: {processor.batch_size}')
    print(f'Cost per candidate: ${processor.estimated_cost_per_candidate}')
except Exception as e:
    print(f'Import error: {e}')
    import traceback
    traceback.print_exc()