# Copyright 2020 IT Projects Labs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ast
import glob
import itertools
import sys

import yaml
from github import Github
from plumbum.cmd import cat

BRANCHES = ["14.0", "13.0", "12.0", "11.0", "10.0", "9.0", "8.0"]
REPOS = {
    "pos-addons": {"extra_branches": ["7.0"]},
    "mail-addons": {},
    "misc-addons": {"extra_branches": ["7.0"]},
    "sync-addons": {},
    "access-addons": {},
    "website-addons": {},
}
ODOO_VERSIONS = ["14.0", "13.0", "12.0", "11.0", "10.0", "9.0", "8.0", "7.0"]


def main(token, repository, branch):
    if branch not in ODOO_VERSIONS:
        return

    config = get_config()
    # TODO: find new modules and mark them with :tada: emoji in README
    store_modules = {m: {"store": True} for m in config.get("addons", [])}
    repo_modules = get_repo_modules()
    modules = dict(
        sorted(dict(**store_modules, **repo_modules).items(), key=lambda item: item[0])
    )
    title = config.get("title")
    if not title:
        github = Github(token)
        repo = github.get_repo(repository)
        title = repo.description
    lines = [
        "[![help@itpp.dev](https://itpp.dev/images/infinity-readme.png)](mailto:help@itpp.dev)",
        "# [{}] {}".format(branch, title),
        "",
    ]

    lines_modules = []
    for m, _data in modules.items():
        lines_modules.append(
            ":heavy_check_mark: [{module}](https://apps.odoo.com/apps/modules/{branch}/{module}/)".format(
                module=m, branch=branch
            )
        )
    lines.append("\n<br/>".join(lines_modules))

    lines += [
        "",
        "Other Addons",
        "============",
        "",
        "| Repository | Versions |",
        "|------------|----------|",
    ]
    for r, data in REPOS.items():
        base_url = "https://github.com/itpp-labs/" + r
        code = "| [itpp-labs/**{}**]({}) | ".format(r, base_url)
        bb = []
        for b in BRANCHES + data.get("extra_branches", []):
            bb.append(
                "[[{branch}]]({base_url}/tree/{branch}#readme)".format(
                    branch=b, base_url=base_url
                )
            )
        code += " ".join(bb)
        code += " |"
        lines.append(code)

    with open("README.md", "w") as readme:
        readme.write("\n".join(lines) + "\n")


def get_repo_modules():
    modules = {}
    for path in itertools.chain(
        glob.glob("*/__manifest__.py"), glob.glob("*/__openerp__.py")
    ):
        manifest = parse_manifest(path)
        m = path.split("/")[0]
        if manifest.get("installable", True):
            modules[m] = {}
    return modules


def get_config():
    try:
        with open(".DINAR/config.yaml") as config_file:
            config = yaml.safe_load(config_file)
    except Exception as e:
        print("Error on parsing .DINAR/config.yaml: %s" % e)
        return {}
    return config.get("repo_readme", {})


def parse_manifest(path):
    try:
        manifest_data = ast.literal_eval(cat(path))
    except Exception as e:
        print("Error on parsing {}: {}".format(path, e))
        manifest_data = {"error": "cannot parse"}
    return manifest_data


def cmd(command, ignore_errors=False):
    print(command)
    try:
        print(command())
    except Exception:
        if not ignore_errors:
            raise


if __name__ == "__main__":
    token = sys.argv[1]
    repository = sys.argv[2]
    branch = sys.argv[3]
    main(token, repository, branch)
