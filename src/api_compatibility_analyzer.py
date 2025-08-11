"""
API Compatibility Analyzer - Main Entry Point
A refactored, modular and maintainable API compatibility analyzer
"""

import os
import sys
import argparse
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from analyzer import CompatibilityChecker, load_api_from_json, ReportGenerator


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser"""
    parser = argparse.ArgumentParser(
        description="API Compatibility Analyzer - Compare two API versions and generate compatibility report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        # Basic usage with JSON output
        python api_compatibility_analyzer.py api_v1.json api_v2.json -o report.json
        
        # Text format output
        python api_compatibility_analyzer.py api_v1.json api_v2.json --format text -o report.txt
        
        # Output to stdout
        python api_compatibility_analyzer.py api_v1.json api_v2.json --format text
        """
    )
    
    parser.add_argument(
        'old_api',
        help='Path to the old API JSON file'
    )
    
    parser.add_argument(
        'new_api', 
        help='Path to the new API JSON file'
    )
    
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Output file path (default: stdout)'
    )
    
    parser.add_argument(
        '--format',
        choices=['json', 'text'],
        default='json',
        help='Output format (default: json)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command line arguments"""
    for api_file in [args.old_api, args.new_api]:
        if not os.path.exists(api_file):
            print(f"Error: API file does not exist: {api_file}")
            sys.exit(1)
        
        if not api_file.endswith('.json'):
            print(f"Warning: Expected JSON file, got: {api_file}")


def main() -> None:
    """Main function for command line interface"""
    # Parse command line arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Validate arguments
    validate_arguments(args)
    
    try:
        # Load API definitions
        if args.verbose:
            print(f"Loading old API from: {args.old_api}")
        old_api = load_api_from_json(args.old_api)
        
        if args.verbose:
            print(f"Loading new API from: {args.new_api}")
        new_api = load_api_from_json(args.new_api)
        
        # Perform compatibility check
        if args.verbose:
            print("Performing compatibility analysis...")
        
        checker = CompatibilityChecker()
        issues = checker.check_compatibility(old_api, new_api)
        summary = checker.generate_summary()
        incompatibility_score = checker.calculate_incompatibility_score()
        
        # Print summary information
        print(f"Analysis complete. Found {summary['total_issues']} issues.")
        print(f"Risk Level: {incompatibility_score.risk_level}")
        print(f"Incompatibility: {incompatibility_score.incompatibility_percentage:.1f}%")
        
        # Generate report
        if args.format == 'json':
            output_content = ReportGenerator.generate_json_report(issues, summary, incompatibility_score)
        else:  # text format
            output_content = ReportGenerator.generate_text_report(issues, summary, incompatibility_score)
        
        # Output result
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_content)
            print(f"Report saved to: {args.output}")
        else:
            print("\n" + output_content)
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
