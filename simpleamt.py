import argparse
import json

import boto3
from jinja2 import Environment, FileSystemLoader


"""
A bunch of free functions that we use in all scripts.
"""


def get_jinja_env(config):
    """
    Get a jinja2 Environment object that we can use to find templates.
    """
    return Environment(loader=FileSystemLoader("."))


def json_file(filename):
    with open(filename, "r") as f:
        return json.load(f)


def get_parent_parser():
    """
    Get an argparse parser with arguments that are always needed
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--prod",
        action="store_false",
        dest="sandbox",
        default=True,
        help="Whether to run on the production AMT site.",
    )
    parser.add_argument("-hf", "--hit_ids_file")
    parser.add_argument(
        "-c", "--config", default="config.json", type=json_file
    )
    return parser


def get_mturk_connection_from_args(args):
    """
    Utility method to get an MTurkConnection from argparse args.
    """
    aws_access_key = args.config.get("aws_access_key")
    aws_secret_key = args.config.get("aws_secret_key")
    return get_mturk_connection(
        sandbox=args.sandbox,
        aws_access_key=aws_access_key,
        aws_secret_key=aws_secret_key,
    )


def get_mturk_connection(
    sandbox=True,
    aws_access_key=None,
    aws_secret_key=None,
    region_name="us-east-1",
):
    """
    Get a boto mturk connection. This is a thin wrapper over boto3.client;
    the only difference is a boolean flag to indicate sandbox or not.
    """
    kwargs = {}
    # boto3 client requires a region to make a connection. if you
    # have a default region in your ~/.aws/config other than us-east-1,
    # it throws an error. Since Mturk endpoint is by default only in
    # us-east-1, there is no point of asking users to provide it. See #29
    kwargs["region_name"] = region_name
    if aws_access_key is not None:
        kwargs["aws_access_key_id"] = aws_access_key
    if aws_secret_key is not None:
        kwargs["aws_secret_access_key"] = aws_secret_key

    if sandbox:
        host = "https://mturk-requester-sandbox.us-east-1.amazonaws.com"
    else:
        host = "https://mturk-requester.us-east-1.amazonaws.com"
    return boto3.client("mturk", endpoint_url=host, **kwargs)
