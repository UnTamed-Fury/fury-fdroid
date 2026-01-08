# App Adder Script (Simplified Version)

This simplified script helps users add new apps to the Fury's F-Droid repository by analyzing a cloned app repository and generating the appropriate `apps.yaml` entry.

## Usage

1. Clone an Android app repository from GitHub:
   ```
   git clone https://github.com/author/app-name.git
   ```

2. Run the app-add script with the cloned repository:
   ```
   python3 app-add.py app-name -gen
   ```

## Example

```
$ git clone https://github.com/aniyomiorg/aniyomi.git
$ python3 app-add.py aniyomi -gen
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

apps.yaml generated successfully!
Added app: Aniyomi (org.aniyomi.app)

Note: This tool only supports GitHub repositories
```

## Important Notes

- This tool **only supports GitHub repositories**
- The script analyzes the cloned repository to extract app information
- It looks for package ID in build.gradle or AndroidManifest.xml files
- It attempts to find app icons in standard Android resource locations
- The generated `apps.yaml` file will contain a single app entry in the correct format
- You will need to manually add this entry to the main `apps.yaml` file in the fury-fdroid repository