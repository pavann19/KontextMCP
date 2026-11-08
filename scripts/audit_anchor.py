import argparse,json
from app.core.anchors import initialize,export_anchor,verify_anchor

def main():
    parser=argparse.ArgumentParser();parser.add_argument("action",choices=["init","export","verify"]);parser.add_argument("--directory");parser.add_argument("--anchor");parser.add_argument("--public-key");parser.add_argument("--log")
    args=parser.parse_args()
    if args.action=="init":print(json.dumps(initialize(args.directory)))
    elif args.action=="export":print(export_anchor(args.directory))
    else:
        valid=verify_anchor(args.anchor,args.public_key,args.log)
        print(json.dumps({"valid":valid}));return 0 if valid else 1
    return 0
if __name__=="__main__":raise SystemExit(main())
