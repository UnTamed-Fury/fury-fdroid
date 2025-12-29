import os, json, yaml, requests, sys

def get_headers(tok):
    h={"Accept":"application/vnd.github.v3+json","User-Agent":"Fury-FDroid-Watcher"}
    if tok: h["Authorization"]=f"token {tok}"
    return h

def check_updates():
    tok=os.environ.get("GH_TOKEN")
    if not tok: sys.exit("GH_TOKEN missing")

    with open("apps.yaml") as f: apps=yaml.safe_load(f)["apps"]
    status_file="release_status.json"
    status=json.load(open(status_file)) if os.path.exists(status_file) else {}
    updates=False

    for app in apps:
        appid=app["id"]; repo=app["url"]
        allow_pre=bool(app.get("fdroid",{}).get("prefer_prerelease",False))
        owner,repo=repo.replace("https://github.com/","").split("/")[:2]

        # unified endpoint → list releases, pick correct newest
        url=f"https://api.github.com/repos/{owner}/{repo}/releases"
        r=requests.get(url,headers=get_headers(tok),timeout=12)
        r.raise_for_status()
        rels=r.json()
        if not rels: continue

        latest=[r for r in rels if r.get("prerelease")==allow_pre]
        if not latest: latest=rels
        latest_tag=latest[0]["tag_name"]

        if status.get(appid)!=latest_tag:
            print(f"★ {appid}: {status.get(appid)} → {latest_tag}")
            status[appid]=latest_tag; updates=True

    json.dump(status,open(status_file,"w"),indent=2)
    print(f"updates_found={'true' if updates else 'false'}")
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"],"a") as f:
            f.write(f"updates_found={'true' if updates else 'false'}\n")

if __name__=="__main__": check_updates()
