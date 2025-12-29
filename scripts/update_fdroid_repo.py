#!/usr/bin/env python3
import os, yaml, requests, subprocess, sys, argparse, shutil

# --- ANDROGUARD IMPORT FIX ---
try:
    from androguard.core.bytecodes.apk import APK
except ImportError:
    try:
        from androguard.core.apk import APK
    except ImportError:
        try:
            from androguard.apk import APK
        except ImportError:
            raise SystemExit("❌ Androguard is installed, but APK class not found. Install correct version.")

APKS="apks"; REPO="fdroid/repo"; MAX_S=2; MAX_P=2

def headers(t):
    return {"Accept":"application/vnd.github.v3+json","Authorization":f"token {t}","User-Agent":"Fury-FDroid-Builder"}

def releases(url,token,pre):
    owner,repo=url.replace("https://github.com/","").split("/")[:2]
    r=requests.get(f"https://api.github.com/repos/{owner}/{repo}/releases",headers=headers(token),timeout=15); r.raise_for_status()
    rels=r.json()
    S=[x for x in rels if not x["prerelease"]][:MAX_S]
    P=[x for x in rels if x["prerelease"]][:MAX_P] if pre else []
    return S,P

def pick(a):
    p=["arm64","universal","v7a","x86_64","x86"]
    for arch in p:
        for i in a:
            if arch in i["name"].lower(): return i
    return a[0]

def sign(fp):
    subprocess.run([
        "fdroid","sign","--force",
        "--keystore=fdroid/keystore.p12",
        f"--storepass={os.environ['FDROID_KEYSTORE_PASS']}",
        f"--keypass={os.environ['FDROID_KEY_PASS']}",
        fp
    ],check=True)

def prune(d):
    ls=sorted(os.listdir(d))
    S=[x for x in ls if "_pre" not in x]
    P=[x for x in ls if "_pre" in x]
    for group,keep in [(S,MAX_S),(P,MAX_P)]:
        for r in group[:-keep]:
            os.remove(os.path.join(d,r))
            print("🗑",r)

def commit():
    subprocess.run(["git","config","user.email","github-actions@github.com"])
    subprocess.run(["git","config","user.name","GitHub Actions"])
    subprocess.run(["git","add",APKS],check=False)
    subprocess.run(["git","commit","-m","Auto: APK Update"],check=False)
    subprocess.run(["git","push"],check=False)

def download():
    t=os.environ.get("GH_TOKEN");
    if not t: sys.exit("GH_TOKEN missing")

    with open("apps.yaml") as f: apps=yaml.safe_load(f)["apps"]
    for app in apps:
        aid,repo,pr=app["id"],app["url"],bool(app.get("fdroid",{}).get("prefer_prerelease",False))
        print("\n📦",aid)
        S,P=releases(repo,t,pr)
        os.makedirs(f"{APKS}/{aid}",exist_ok=True)

        for group,is_pre in [(S,False),(P,True)]:
            for rel in group:
                asset=pick([x for x in rel["assets"] if x["name"].endswith(".apk")])
                tmp=f"{APKS}/{aid}/tmp.apk"
                with requests.get(asset["browser_download_url"],stream=True) as r:
                    r.raise_for_status()
                    with open(tmp,"wb") as f: [f.write(c) for c in r.iter_content(8192)]
                v=APK(tmp).get_androidversion_code()
                suffix="_pre" if is_pre else ""
                final=f"{APKS}/{aid}/{aid}_{v}{suffix}.apk"
                os.rename(tmp,final); sign(final)

        prune(f"{APKS}/{aid}")
    commit()

def index():
    if os.path.exists(REPO): shutil.rmtree(REPO)
    os.makedirs(REPO)
    for r,_,fs in os.walk(APKS):
        for f in fs:
            if f.endswith(".apk"):
                shutil.copy2(os.path.join(r,f),REPO)
    subprocess.run(["fdroid","update","--create-metadata","--pretty","--verbose"],cwd="fdroid",check=True)

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--download",action="store_true"); p.add_argument("--index",action="store_true")
    a=p.parse_args()
    if a.download: download()
    if a.index: index()
