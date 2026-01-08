# Universal App Adder Script

This unified script helps users add new apps to the Fury's F-Droid repository. It supports two modes:

1. **Auto-analysis mode**: Analyze a cloned repository to extract app information automatically
2. **Manual mode**: Interactively ask for app information

## Usage

### Auto-analysis Mode
Analyze a cloned repository to extract app information:

```
python3 universal-app-add.py <app-repo> -analyze
```

### Manual Mode
Enter app information manually:

```
python3 universal-app-add.py -manual
```

## Example (Auto-analysis)

```
$ git clone https://github.com/aniyomiorg/aniyomi.git
$ python3 universal-app-add.py aniyomi -analyze
Analyzing repository: aniyomi
App name: Aniyomi
Package ID: org.aniyomi.app
GitHub URL: https://github.com/aniyomiorg/aniyomi
Icon URL: https://raw.githubusercontent.com/aniyomiorg/aniyomi/main/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png

Select app category:
1. System
2. Entertainment
3. Development
4. Communication
5. Security
6. Gaming
7. Misc
Enter category number (1-7): 2

Select app status:
1. Stable
2. Alpha
3. Beta
4. Nightly
5. Discontinued
6. Maintained Fork
7. Active
Enter status number (1-7): 7
Content type (e.g., Manga, Anime, Music, Video, etc. - press Enter to skip): Manga, Anime
Prefer prerelease versions? (y/n): n

App entry generated for: Aniyomi (org.aniyomi.app)
Copy and paste this entry into your apps.yaml file under the 'apps:' section:

--------------------------------------------------
- id: org.aniyomi.app
  name: Aniyomi
  author: aniyomiorg
  url: https://github.com/aniyomiorg/aniyomi
  classification:
    domain: Entertainment
    type: Entertainment
    content: Manga, Anime
    status: Active
  assets:
    icon:
      type: github-repo
      url: https://raw.githubusercontent.com/aniyomiorg/aniyomi/main/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png
  fdroid:
    categories:
    - Entertainment
    - Manga, Anime
    prefer_prerelease: false

--------------------------------------------------

Note: This tool only supports GitHub repositories
```

## Example (Manual)

```
$ python3 universal-app-add.py -manual
Running in manual mode...
App Adder for Fury's F-Droid Repository
========================================
App name: My Awesome App
Package ID: com.example.awesome
GitHub URL: https://github.com/example/my-awesome-app
Icon URL (project-root/icon-path or GitHub raw URL): https://raw.githubusercontent.com/example/my-awesome-app/main/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png

Select app category:
1. System
2. Entertainment
3. Development
4. Communication
5. Security
6. Gaming
7. Misc
Enter category number (1-7): 3

Select app status:
1. Stable
2. Alpha
3. Beta
4. Nightly
5. Discontinued
6. Maintained Fork
7. Active
Enter status number (1-7): 1
Content type (e.g., Manga, Anime, Music, Video, etc. - press Enter to skip): 
Prefer prerelease versions? (y/n): n
Archive old versions? (y/n): n

App entry generated for: My Awesome App (com.example.awesome)
Copy and paste this entry into your apps.yaml file under the 'apps:' section:
...
```

## Important Notes

- This tool **only supports GitHub repositories**
- The script generates a YAML entry that can be copied to the main `apps.yaml` file
- Both auto-analysis and manual modes produce the same output format
- The generated entry follows the fury-fdroid repository format