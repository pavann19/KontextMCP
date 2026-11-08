"""Explicit schema deployment: upgrade or verify, without inserting demo records."""
import argparse
from app.db.session import engine
from app.db.migrations import upgrade_schema, verify_schema


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("upgrade", "check"))
    args = parser.parse_args()
    with engine.begin() as connection:
        if args.operation == "upgrade":
            upgrade_schema(connection)
        verify_schema(connection)
    print("Schema is at the reviewed migration head and matches the application metadata.")


if __name__ == "__main__":
    main()
