import argparse,json
from pathlib import Path
from app.core.retention import inventory,quarantine,restore,apply_reviewed
ROOT=Path(__file__).resolve().parents[1]
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("action",choices=["inventory","quarantine","restore","apply"]);parser.add_argument("--directory");parser.add_argument("--output");parser.add_argument("--confirm-reviewed",action="store_true")
    args=parser.parse_args()
    if args.action=="inventory":result=inventory(ROOT)
    elif args.action=="quarantine":result=quarantine(ROOT,args.directory)
    elif args.action=="restore":result=restore(args.directory,args.output)
    else:result=apply_reviewed(ROOT,args.directory,args.confirm_reviewed)
    print(json.dumps(result,indent=2))
