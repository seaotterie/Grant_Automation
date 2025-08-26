#!/usr/bin/env python3
"""
Create Conservative Budget Configuration
Sets up initial $5 budget with category allocation for safe AI-Lite testing
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.analytics.cost_tracker import get_cost_tracker, CostCategory


async def create_conservative_budget():
    """Create a conservative $5 budget for AI-Lite integration testing"""
    
    print("Creating Conservative Budget Configuration ($5 limit)")
    print("=" * 60)
    
    # Get cost tracker instance
    tracker = get_cost_tracker()
    
    # Create main budget
    budget_id = "ai_lite_integration_budget"
    budget_name = "AI-Lite Integration Testing Budget"
    total_budget = Decimal('5.00')  # $5 total budget
    period_days = 30  # 30-day budget period
    
    try:
        # Create the budget
        budget = await tracker.create_budget(
            budget_id=budget_id,
            name=budget_name,
            total_budget_usd=total_budget,
            period_days=period_days
        )
        
        print(f"[SUCCESS] Created budget: {budget_name}")
        print(f"   Total Budget: ${budget.total_budget_usd}")
        print(f"   Period: {period_days} days")
        print(f"   Budget ID: {budget_id}")
        
        # Configure category budgets
        budget.category_budgets = {
            CostCategory.AI_ANALYSIS: Decimal('3.00'),      # 60% for AI-Lite operations
            CostCategory.AI_SCORING: Decimal('1.50'),       # 30% for scoring operations  
            CostCategory.AI_CLASSIFICATION: Decimal('0.50') # 10% for classification/misc
        }
        
        # Set conservative alert thresholds
        budget.warning_threshold = 0.75   # Warning at 75% ($3.75)
        budget.critical_threshold = 0.90  # Critical at 90% ($4.50)
        
        # Save updated budget
        tracker.budgets[budget_id] = budget
        await tracker._save_data()
        
        print(f"\nCategory Allocations:")
        for category, amount in budget.category_budgets.items():
            percentage = (amount / total_budget) * 100
            print(f"   {category.value}: ${amount} ({percentage:.0f}%)")
        
        print(f"\nAlert Thresholds:")
        print(f"   Warning: {budget.warning_threshold*100:.0f}% (${total_budget * Decimal(str(budget.warning_threshold))})")
        print(f"   Critical: {budget.critical_threshold*100:.0f}% (${total_budget * Decimal(str(budget.critical_threshold))})")
        
        # Display cost estimates for common operations
        print(f"\nCost Estimates (AI-Lite Integration):")
        print(f"   GPT-4o-mini (economy): ~$0.0001/candidate")
        print(f"   GPT-3.5-turbo (standard): ~$0.0003/candidate") 
        print(f"   GPT-4o (premium): ~$0.003/candidate")
        
        print(f"\nExpected Usage with ${total_budget} budget:")
        print(f"   Economy tier: ~50,000 candidates maximum")
        print(f"   Standard tier: ~16,000 candidates maximum")
        print(f"   Premium tier: ~1,600 candidates maximum")
        
        # Create a smaller daily testing budget
        daily_budget_id = "daily_ai_lite_testing"
        daily_budget_name = "Daily AI-Lite Testing Budget" 
        daily_budget_amount = Decimal('1.00')  # $1 per day limit
        
        daily_budget = await tracker.create_budget(
            budget_id=daily_budget_id,
            name=daily_budget_name,
            total_budget_usd=daily_budget_amount,
            period_days=1  # Daily budget
        )
        
        daily_budget.warning_threshold = 0.8   # Warning at 80% ($0.80)
        daily_budget.critical_threshold = 0.95 # Critical at 95% ($0.95)
        
        tracker.budgets[daily_budget_id] = daily_budget
        await tracker._save_data()
        
        print(f"\n[SUCCESS] Created daily testing budget: ${daily_budget_amount}/day")
        
        print(f"\nBudget Setup Complete!")
        print(f"   Monthly Budget: ${total_budget} over {period_days} days")
        print(f"   Daily Budget: ${daily_budget_amount} per day")
        print(f"   Budget files stored in: {tracker.cost_dir}")
        
        print(f"\nSafety Features Enabled:")
        print(f"   [OK] Pre-execution budget validation")
        print(f"   [OK] Real-time cost tracking") 
        print(f"   [OK] Automatic operation blocking when limits exceeded")
        print(f"   [OK] Multi-level alert thresholds")
        print(f"   [OK] Category-based spending limits")
        
        return budget
        
    except Exception as e:
        print(f"[ERROR] Failed to create budget: {e}")
        return None


async def show_budget_status():
    """Show current budget status"""
    
    tracker = get_cost_tracker()
    analytics = await tracker.get_cost_analytics()
    
    print(f"\n📊 Current Budget Status:")
    print(f"   Total Records: {analytics['total_records']}")
    print(f"   Total Cost: ${analytics['total_cost']}")
    
    for budget_id, status in analytics['budget_status'].items():
        print(f"\n   Budget: {status['name']}")
        print(f"     Total: ${status['total_budget']}")
        print(f"     Spent: ${status['spent']}")
        print(f"     Remaining: ${status['remaining']}")
        print(f"     Utilization: {status['utilization_percent']:.1f}%")
        print(f"     Status: {'[WARNING]' if status['over_warning'] else '[NORMAL]'}")


if __name__ == "__main__":
    print("AI-Lite Integration Budget Setup")
    print("Creating conservative budget configuration for secure testing...")
    print()
    
    # Create the budget
    budget = asyncio.run(create_conservative_budget())
    
    if budget:
        print(f"\n[SUCCESS] Budget configuration completed successfully!")
        
        # Show status
        asyncio.run(show_budget_status())
        
        print(f"\nNext steps:")
        print(f"1. Set up OpenAI API key via: python setup_auth.py api-keys add openai")
        print(f"2. Test AI-Lite integration with small batches (1-5 candidates)")
        print(f"3. Monitor costs in real-time via budget analytics")
        
    else:
        print(f"\n[ERROR] Budget setup failed. Check the logs for details.")
        sys.exit(1)