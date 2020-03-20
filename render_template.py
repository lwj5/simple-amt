import argparse

import simpleamt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(parents=[simpleamt.get_parent_parser()])
    parser.add_argument("-t", "--html_template", required=True)
    parser.add_argument("-o", "--rendered_html", required=True)
    args = parser.parse_args()

    env = simpleamt.get_jinja_env(args.config)
    template = env.get_template(args.html_template)

    html = template.render({"input": ""})
    with open(args.rendered_html, "w") as f:
        f.write(html)
