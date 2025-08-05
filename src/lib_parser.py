import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from parser import APIParser, parse_arguments


def main():
    """Main entry point."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Create and configure the parser
        api_parser = APIParser(verbose=args.verbose, exclude_dirs=args.exclude_dirs)
        
        # Parse the library
        success = api_parser.parse_with_build_system(
            root_path=args.root_path,
            build_system=args.build_system,
            build_dir=args.build_dir,
            target=args.target,
            manual_flags=args.compile_flags,
            output_path=args.output_path
        )
        
        if success:
            print(f"Successfully parsed library and saved API data to {args.output_path}")
        else:
            print("Failed to parse library")
            sys.exit(1)

    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
