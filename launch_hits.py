import argparse
import json
import random
import sys
from os import listdir
from os.path import isfile, join

import simpleamt


def launch_hit(hit_input):
    template_params = {"input": json.dumps(hit_input)}
    html_doc = template.render(template_params)
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
        html_doc,
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
        print("Require a input_json_file or input_json_directory")
        sys.exit()

    mtc = simpleamt.get_mturk_connection_from_args(args)

    hit_properties = json.load(args.hit_properties_file)
    hit_properties["Reward"] = str(hit_properties["Reward"])
    simpleamt.setup_qualifications(hit_properties, mtc)

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
            with open(f, "r") as f_stream:
                json_obj = json.loads("[" + f_stream.read() + "]")
                for i, hit_input in enumerate(json_obj):
                    hit_id = launch_hit(hit_input)
                    hit_ids_file.write("%s\n" % hit_id)
                    print("Launched HIT ID: %s, %d" % (hit_id, i + 1))
