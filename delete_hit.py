import argparse

import simpleamt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        parents=[simpleamt.get_parent_parser()], description="Delete HITs"
    )
    parser.add_argument("--hit_id")
    args = parser.parse_args()
    mtc = simpleamt.get_mturk_connection_from_args(args)
    hit_id = args.hit_id

    print(
        "This will delete HIT with ID: %s with sandbox=%s"
        % (hit_id, str(args.sandbox))
    )
    print("Continue?")
    s = input("(y/N): ")
    if s.strip().lower() == "y":
        try:
            mtc.delete_hit(HITId=hit_id)
        except Exception as e:
            print("Failed to delete: %s" % (hit_id))
            print(e)
    else:
        print("Aborting")
