import time
import datetime
import json
import os
import pathlib

import argparse
import requests


parser = argparse.ArgumentParser()

parser.add_argument("login", type=str, help="Account name")
parser.add_argument("password", type=str, help="Account name")
parser.add_argument("namespace", type=str, help="namespace of repository")
parser.add_argument("repository", type=str, help="repository name")
parser.add_argument("updater", type=str, help="updater script path")


if __name__ == "__main__":
    args = parser.parse_args()

    PYTHON_UPDATE_SCRIPT_PATH = pathlib.Path(args.updater)
    NAMESPACE = args.namespace
    ALIVE = True

    if not PYTHON_UPDATE_SCRIPT_PATH.exists():
        raise pathlib.PathNotFoundError("no such script")

    token_response = requests.post("https://hub.docker.com/v2/users/login/",
                                      data={
                                        "username": args.login,
                                        "password": args.password
                                      })

    if token_response.status_code in [200, 201]:
        TOKEN = json.loads(token_response.text)["token"]

        print("successfully logged in.")
        print(f"watching repository {args.namespace}/{args.repository}...")

        HEADERS = {"Authorization": F"Bearer {TOKEN}"}
        last_updated = datetime.datetime.now() - datetime.timedelta(weeks=1000)

        while ALIVE:
            url = f"https://hub.docker.com/v2/namespaces/{args.namespace}/repositories/{args.repository}/images"
            traceback = requests.get(url, headers=HEADERS)

            if traceback.status_code == 200:
                last_pushed = datetime.datetime.strptime(
                    [el["last_pushed"] for el in sorted(json.loads(traceback.text)["results"],
                                                        key=lambda el: datetime.datetime.strptime(
                                                            el["last_pushed"].split(".")[0], '%Y-%m-%dT%H:%M:%S'))][-1]
                                                            .split(".")[0], '%Y-%m-%dT%H:%M:%S')

                if last_updated < last_pushed:
                    print(f"[{last_pushed}] remote repository has been updated.")
                    last_updated = last_pushed
                    os.system(f"python3 {PYTHON_UPDATE_SCRIPT_PATH}")

                time.sleep(10)

