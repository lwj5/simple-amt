import argparse
import json
import random
import sys
from os import listdir
from os.path import isfile, join, split

import htmlmin

import simpleamt


def setup_qualifications(hit_properties):
    """
    Replace some of the human-readable keys from the raw HIT properties
    JSON data structure with boto-specific objects.
    """
    qual = []
    if "Qualifications" in hit_properties:
        for qualification in hit_properties["Qualifications"]:
            if (
                "QualificationTypeId" in qualification
                and "Comparator" in qualification
            ):
                comparator = qualification["Comparator"]
                available_comparators = [
                    "LessThan",
                    "LessThanOrEqualTo",
                    "GreaterThan",
                    "GreaterThanOrEqualTo",
                    "EqualTo",
                    "NotEqualTo",
                    "Exists",
                    "DoesNotExist",
                    "In",
                    "NotIn",
                ]
                if comparator not in available_comparators:
                    print(
                        "The 'qualification comparator' is not one of {}".format(
                            available_comparators
                        )
                    )
                    sys.exit(1)
                qual.append(qualification)
        del hit_properties["Qualifications"]

    if "Country" in hit_properties:
        qual.append(
            {
                "QualificationTypeId": "00000000000000000071",
                "Comparator": "In",
                "LocaleValues": [
                    {"Country": country}
                    for country in hit_properties["Country"]
                ],
            }
        )
        del hit_properties["Country"]

    if "HitsApproved" in hit_properties:
        qual.append(
            {
                "QualificationTypeId": "00000000000000000040",
                "Comparator": "GreaterThan",
                "IntegerValues": [hit_properties["HitsApproved"]],
            }
        )
        del hit_properties["HitsApproved"]

    if "PercentApproved" in hit_properties:
        qual.append(
            {
                "QualificationTypeId": "000000000000000000L0",
                "Comparator": "GreaterThan",
                "IntegerValues": [hit_properties["PercentApproved"]],
            }
        )
        del hit_properties["PercentApproved"]

    hit_properties["QualificationRequirements"] = qual


def launch_hit(hit_input, mtc):
    template_params = {"input": json.dumps(hit_input)}
    html_doc = template.render(template_params)
    minified_html_doc = htmlmin.minify(html_doc, remove_empty_space=True)
    html_question = """
    <HTMLQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2011-11-11/HTMLQuestion.xsd">
        <HTMLContent>
            <![CDATA[
                <!DOCTYPE html>
                %s
            ]]>
        </HTMLContent>
        <FrameHeight>%d</FrameHeight>
    </HTMLQuestion>
    """ % (
        minified_html_doc,
        frame_height,
    )
    hit_properties["Question"] = html_question

    # This error handling is kinda hacky.
    # TODO: Do something better here.
    launched = False
    while not launched:
        try:
            boto_hit = mtc.create_hit(**hit_properties)
            launched = True
        except Exception as e:
            print(e)
            return None
    return boto_hit["HIT"]["HITId"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(parents=[simpleamt.get_parent_parser()])
    parser.add_argument(
        "-p",
        "--hit_properties_file",
        type=argparse.FileType("r"),
        required=True,
    )
    parser.add_argument(
        "-t", "--html_template", required=True,
    )
    parser.add_argument("-f", "--input_json_file")
    parser.add_argument("-d", "--input_json_directory")
    args = parser.parse_args()

    if args.hit_ids_file is None:
        print("Need to input a hit_ids_file")
        sys.exit()

    if not args.input_json_file and not args.input_json_directory:
        print("Either a input_json_file or input_json_directory is required")
        sys.exit()

    mtc = simpleamt.get_mturk_connection_from_args(args)
    hit_properties = json.load(args.hit_properties_file)
    hit_properties["Reward"] = str(hit_properties["Reward"])
    setup_qualifications(hit_properties)

    frame_height = hit_properties.pop("FrameHeight")
    env = simpleamt.get_jinja_env(args.config)
    template = env.get_template(args.html_template)

    with open(args.hit_ids_file, "a+") as hit_ids_file:
        if args.input_json_directory:
            files = [
                join(args.input_json_directory, f)
                for f in listdir(args.input_json_directory)
                if isfile(join(args.input_json_directory, f))
            ]
            random.shuffle(files)
        else:
            files = [args.input_json_file]

        for f in files:
            _, filename = split(f)
            if filename.lower() == ".ds_store":
                continue

            with open(f, "r") as f_stream:
                print("Reading {}".format(f))
                json_obj = json.loads(f_stream.read())
                for i, hit_input in enumerate(json_obj):
                    hit_id = launch_hit(hit_input, mtc)
                    if hit_id:
                        hit_ids_file.write("%s\n" % hit_id)
                        print("Launched HIT ID: %s, %d" % (hit_id, i + 1))
                    else:
                        print("Launched HIT ID Failed: %d" % (i + 1))
