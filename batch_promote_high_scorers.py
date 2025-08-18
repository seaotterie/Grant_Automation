#!/usr/bin/env python3
"""
Batch Promotion Script for High-Scoring Opportunities
Promote existing opportunities with 75%+ scores to qualified_prospects stage

This script:
1. Finds all opportunities with compatibility_score >= 0.75
2. Updates their pipeline_stage from discovery to pre_scoring (qualified_prospects)
3. Updates the file names to reflect new stage
4. Provides detailed reporting of promotions
"""

import json
import os
from pathlib import Path
from typing import List, Dict
import logging
from datetime import datetime
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BatchPromotion:
    def __init__(self, data_dir: str = "data/profiles"):
        self.data_dir = Path(data_dir)
        self.leads_dir = self.data_dir / "leads"
        
        self.stats = {
            'total_leads_checked': 0,
            'high_scorers_found': 0,
            'promotions_completed': 0,
            'already_promoted': 0,
            'promotion_errors': 0,
            'promoted_opportunities': []
        }
        
    def run_batch_promotion(self):
        """Run batch promotion for high-scoring opportunities"""
        logger.info("Starting batch promotion for high-scoring opportunities...")
        
        # Find high-scoring opportunities in discovery stage
        high_scorers = self._find_high_scoring_opportunities()
        
        # Promote each high scorer
        for lead_info in high_scorers:
            try:
                self._promote_opportunity(lead_info)
            except Exception as e:
                logger.error(f"Error promoting {lead_info['lead_id']}: {e}")
                self.stats['promotion_errors'] += 1
        
        self._print_promotion_summary()
        
    def _find_high_scoring_opportunities(self) -> List[Dict]:
        """Find opportunities with score >= 0.75 in discovery stage"""
        logger.info("Scanning for high-scoring opportunities...")
        
        high_scorers = []
        
        for lead_file in self.leads_dir.glob("*.json"):
            self.stats['total_leads_checked'] += 1
            
            try:
                with open(lead_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                score = data.get("compatibility_score", 0.0)
                stage = data.get("pipeline_stage", "discovery")
                org_name = data.get("organization_name", "Unknown")
                
                # Check if this is a high scorer in discovery stage
                if score >= 0.75 and stage == "discovery":
                    high_scorers.append({
                        'file_path': lead_file,
                        'data': data,
                        'lead_id': data.get('lead_id'),
                        'score': score,
                        'org_name': org_name,
                        'profile_id': data.get('profile_id')
                    })
                    
                    logger.info(f"Found high scorer: {org_name} - {score:.1%} (Lead: {data.get('lead_id')})")
                    self.stats['high_scorers_found'] += 1
                    
                elif score >= 0.75 and stage != "discovery":
                    # Already promoted
                    self.stats['already_promoted'] += 1
                    logger.debug(f"Already promoted: {org_name} - {score:.1%} (Stage: {stage})")
                    
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Error processing {lead_file}: {e}")
        
        logger.info(f"Found {len(high_scorers)} high-scoring opportunities in discovery stage")
        return high_scorers
        
    def _promote_opportunity(self, lead_info: Dict):
        """Promote a single opportunity to qualified_prospects stage"""
        lead_id = lead_info['lead_id']
        data = lead_info['data']
        old_file = lead_info['file_path']
        
        # Update the opportunity data
        data['pipeline_stage'] = 'pre_scoring'  # This maps to qualified_prospects in UI
        data['last_analyzed'] = datetime.now().isoformat()
        
        # Add promotion metadata
        if 'match_factors' not in data:
            data['match_factors'] = {}
        data['match_factors']['auto_promoted'] = True
        data['match_factors']['promotion_reason'] = f"Auto-promoted for high score: {lead_info['score']:.1%}"
        data['match_factors']['promoted_at'] = datetime.now().isoformat()
        
        # Create new filename with updated stage
        new_filename = f"{lead_id}_{data.get('profile_id', 'unknown')}_pre_scoring.json"
        new_file = self.leads_dir / new_filename
        
        # Write updated data to new file
        with open(new_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        # Remove old file if it has a different name
        if old_file.name != new_filename:
            old_file.unlink()
            
        # Track the promotion
        self.stats['promotions_completed'] += 1
        self.stats['promoted_opportunities'].append({
            'lead_id': lead_id,
            'organization_name': lead_info['org_name'],
            'score': lead_info['score'],
            'profile_id': lead_info['profile_id'],
            'old_stage': 'discovery',
            'new_stage': 'pre_scoring',
            'promoted_at': datetime.now().isoformat()
        })
        
        logger.info(f"✅ Promoted {lead_info['org_name']} ({lead_info['score']:.1%}) to qualified_prospects")
        
    def _print_promotion_summary(self):
        """Print comprehensive promotion summary"""
        print("\n" + "="*60)
        print("BATCH PROMOTION SUMMARY")
        print("="*60)
        print(f"Total leads checked:           {self.stats['total_leads_checked']}")
        print(f"High scorers found (75%+):     {self.stats['high_scorers_found']}")
        print(f"Already promoted:              {self.stats['already_promoted']}")
        print(f"Promotions completed:          {self.stats['promotions_completed']}")
        print(f"Promotion errors:              {self.stats['promotion_errors']}")
        print("-" * 60)
        
        if self.stats['promoted_opportunities']:
            print("\nPROMOTED OPPORTUNITIES:")
            print("-" * 60)
            for promo in self.stats['promoted_opportunities']:
                print(f"• {promo['organization_name'][:40]:<40} {promo['score']:.1%} → qualified_prospects")
        
        print("\nIMPACT:")
        if self.stats['promotions_completed'] > 0:
            print(f"✅ {self.stats['promotions_completed']} opportunities now eligible for PLAN tab")
            print("✅ High scorers will now appear in qualified_prospects filter")
            print("✅ Auto-promotion system is working for future discoveries")
        else:
            print("ℹ️  No promotions needed - all high scorers already promoted")
            
        print("\nNEXT STEPS:")
        print("1. 🔄 Refresh web interface to see promoted opportunities on PLAN tab")
        print("2. 🎯 Review promoted opportunities for strategic planning")
        print("3. 📈 Monitor auto-promotion working for new discoveries")
        print("="*60)


if __name__ == "__main__":
    promotion = BatchPromotion()
    promotion.run_batch_promotion()