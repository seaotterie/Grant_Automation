#!/usr/bin/env python3
"""
Test script for the Data Quality Validator
Demonstrates comprehensive data quality analysis across the entity database.
"""

import asyncio
import json
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.data_quality_validator import get_data_quality_validator, DataQualityLevel


async def main():
    """Run comprehensive data quality validation test."""
    print("Starting Comprehensive Data Quality Validation")
    print("=" * 60)
    
    # Initialize validator
    validator = get_data_quality_validator()
    
    try:
        # Run validation on all entities
        print("Analyzing all entity types...")
        reports = await validator.validate_all_entities()
        
        print(f"\nValidation complete! Generated {len(reports)} reports")
        print("=" * 60)
        
        # Display summary for each entity type
        for entity_type, report in reports.items():
            print(f"\n{entity_type.upper()} REPORT")
            print("-" * 40)
            print(f"Total Entities: {report.total_entities}")
            print(f"Quality Level: {report.quality_level.value.upper()}")
            print(f"Overall Score: {report.overall_score:.2%}")
            print(f"Completeness: {report.completeness_score:.2%}")
            print(f"Accuracy: {report.accuracy_score:.2%}")
            print(f"Consistency: {report.consistency_score:.2%}")
            print(f"Freshness: {report.freshness_score:.2%}")
            
            # Show top issues
            if report.issues:
                print(f"\nIssues Found ({len(report.issues)}):")
                for issue in report.issues[:3]:  # Show top 3
                    print(f"  - {issue.severity.upper()}: {issue.description}")
                if len(report.issues) > 3:
                    print(f"  ... and {len(report.issues) - 3} more")
            else:
                print("\nNo issues found!")
            
            # Show recommendations
            if report.recommendations:
                print(f"\nRecommendations:")
                for rec in report.recommendations[:2]:  # Show top 2
                    print(f"  - {rec}")
        
        # Overall system summary
        print("\n" + "=" * 60)
        print("SYSTEM-WIDE SUMMARY")
        print("-" * 40)
        
        total_entities = sum(r.total_entities for r in reports.values() if r.total_entities > 0)
        avg_score = sum(r.overall_score for r in reports.values()) / len(reports) if reports else 0
        total_issues = sum(len(r.issues) for r in reports.values())
        
        print(f"Total Entities Validated: {total_entities}")
        print(f"Average Quality Score: {avg_score:.2%}")
        print(f"Total Issues Found: {total_issues}")
        
        # Quality assessment
        if avg_score >= 0.9:
            quality_msg = "EXCELLENT - System data quality is outstanding"
        elif avg_score >= 0.75:
            quality_msg = "GOOD - System data quality meets standards"
        elif avg_score >= 0.6:
            quality_msg = "FAIR - Some data quality improvements needed"
        else:
            quality_msg = "POOR - Significant data quality issues require attention"
        
        print(f"\n{quality_msg}")
        
        # Save detailed report
        output_file = Path("data_quality_report.json")
        report_data = {
            "generated_at": reports[list(reports.keys())[0]].generated_at.isoformat(),
            "summary": {
                "total_entities": total_entities,
                "average_score": avg_score,
                "total_issues": total_issues
            },
            "reports": {
                entity_type: {
                    "total_entities": report.total_entities,
                    "quality_level": report.quality_level.value,
                    "scores": {
                        "overall": report.overall_score,
                        "completeness": report.completeness_score,
                        "accuracy": report.accuracy_score,
                        "consistency": report.consistency_score,
                        "freshness": report.freshness_score
                    },
                    "issues_count": len(report.issues),
                    "recommendations": report.recommendations
                } for entity_type, report in reports.items()
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\nDetailed report saved to: {output_file}")
        print("\nData quality validation complete!")
        
    except Exception as e:
        print(f"Error during validation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())