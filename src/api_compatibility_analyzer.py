"""
API Compatibility Analyzer - Main Entry Point
A refactored, modular and maintainable API compatibility analyzer
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from analyzer import CompatibilityChecker, load_api_from_json, ReportGenerator


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure logging format
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(console_handler)
    
    # Prevent duplicate logs
    logger.propagate = False


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
    logger = logging.getLogger(__name__)
    
    for api_file in [args.old_api, args.new_api]:
        if not os.path.exists(api_file):
            logger.error(f"API file does not exist: {api_file}")
            sys.exit(1)
        
        if not api_file.endswith('.json'):
            logger.warning(f"Expected JSON file, got: {api_file}")


def main() -> None:
    """Main function for command line interface"""
    # Parse command line arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Setup logging based on verbose flag
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Validate arguments
    validate_arguments(args)
    
    try:
        # Load API definitions
        logger.debug(f"Loading old API from: {args.old_api}")
        old_api = load_api_from_json(args.old_api)
        
        logger.debug(f"Loading new API from: {args.new_api}")
        new_api = load_api_from_json(args.new_api)
        
        # Perform compatibility check
        logger.debug("Performing compatibility analysis...")
        
        checker = CompatibilityChecker()
        issues = checker.check_compatibility(old_api, new_api)
        summary = checker.generate_summary()
        incompatibility_score = checker.calculate_incompatibility_score()
        
        # Log summary information
        logger.info(f"Analysis complete. Found {summary['total_issues']} issues.")
        logger.info(f"Incompatibility: {incompatibility_score.incompatibility_percentage:.1f}%")
        
        # Log detailed old API breakage information in debug mode
        logger.debug("="*60)
        logger.debug("OLD API BREAKAGE ANALYSIS")
        logger.debug("="*60)
        logger.debug(f"Total old API elements: {incompatibility_score.old_api_count}")
        logger.debug(f"Broken old API elements: {incompatibility_score.broken_old_api_count}")
        logger.debug(f"Old API breakage percentage: {incompatibility_score.old_api_breakage_percentage:.2f}%")
            
        # Show breakdown of what types of elements are broken
        broken_elements = checker._get_broken_old_api_breakdown()
        if broken_elements:
            logger.debug("Broken API breakdown:")
            for element_type, count in broken_elements.items():
                logger.debug(f"  - {element_type.title()}: {count}")
        logger.debug("="*60)
        
        # Generate report
        if args.format == 'json':
            output_content = ReportGenerator.generate_json_report(issues, summary, incompatibility_score)
        else:  # text format
            output_content = ReportGenerator.generate_text_report(issues, summary, incompatibility_score)
        
        # Output result
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_content)
            logger.info(f"Report saved to: {args.output}")
        else:
            print(output_content)  # Keep stdout output for report content
            
    except Exception as e:
        logger.exception(f"Error during analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
