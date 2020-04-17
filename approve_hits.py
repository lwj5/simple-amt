import argparse
import json
import re

import simpleamt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(parents=[simpleamt.get_parent_parser()])
    parser.add_argument("-f", action="store_true", default=False)
    args = parser.parse_args()
    mtc = simpleamt.get_mturk_connection_from_args(args)

    approve_ids = set()
    reject_ids = set()

    if args.hit_ids_file is None:
        parser.error("Must specify --hit_ids_file.")

    with open(args.hit_ids_file, "r") as f:
        hit_ids = [line.strip() for line in f]

    for hit_id in hit_ids:
        paginator = mtc.get_paginator("list_assignments_for_hit")
        try:
            for a_page in paginator.paginate(
                HITId=hit_id, PaginationConfig={"PageSize": 100}
            ):
                for a in a_page["Assignments"]:
                    if a["AssignmentStatus"] == "Submitted":
                        try:
                            # Try to parse the output from the assignment.
                            # If it isn't
                            # valid JSON then we reject the assignment.
                            json.loads(
                                re.search(
                                    r"<FreeText>(?P<answer>.*?)</FreeText>",
                                    a["Answer"],
                                )["answer"]
                            )
                            approve_ids.add(a["AssignmentId"])
                        except ValueError as e:
                            reject_ids.add(["AssignmentId"])
                            print(e)
                    else:
                        print(
                            "hit {} - {} has already been {}".format(
                                hit_id,
                                a["AssignmentId"],
                                a["AssignmentStatus"],
                            )
                        )
        except mtc.exceptions.RequestError:
            continue

    print(
        "This will approve {} assignments and reject {} assignments with sandbox={}".format(
            len(approve_ids), len(reject_ids), args.sandbox
        )
    )
    print("Continue?")

    if not args.f:
        s = input("(y/N): ")
    else:
        s = "Y"
    if s.strip().lower() == "y":
        print("Approving assignments")
        for idx, assignment_id in enumerate(approve_ids):
            print("Approving assignment %d / %d" % (idx + 1, len(approve_ids)))
            mtc.approve_assignment(AssignmentId=assignment_id)
        for idx, assignment_id in enumerate(reject_ids):
            print("Rejecting assignment %d / %d" % (idx + 1, len(reject_ids)))
            mtc.reject_assignment(
                AssignmentId=assignment_id, RequesterFeedback="Invalid results"
            )
    else:
        print("Aborting")
