import argparse

import simpleamt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(parents=[simpleamt.get_parent_parser()])
    parser.add_argument("-f", action="store_true", default=False)
    parser.add_argument("-b", "--bonus", required=True)
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()
    mtc = simpleamt.get_mturk_connection_from_args(args)

    assignment_worker_set = set()

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
                    if a["AssignmentStatus"] == "Approved":
                        assignment_worker_set.add(
                            (a["AssignmentId"], a["WorkerId"])
                        )
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
        'This will send bonus of ${} to {} assignments with reason "{}". Sandbox={}'.format(
            args.bonus, len(assignment_worker_set), args.reason, args.sandbox
        )
    )
    print("Continue?")

    if not args.f:
        s = input("(y/N): ")
    else:
        s = "Y"
    if s.strip().lower() == "y":
        print("Sending bonus")
        for idx, (assignment_id, worker_id) in enumerate(
            assignment_worker_set
        ):
            print(
                "Sending bonus to {} for assignment {} ({} / {})".format(
                    worker_id,
                    assignment_id,
                    idx + 1,
                    len(assignment_worker_set),
                )
            )
            mtc.send_bonus(
                WorkerId=worker_id,
                BonusAmount=args.bonus,
                AssignmentId=assignment_id,
                Reason=args.reason,
            )
    else:
        print("Aborting")
