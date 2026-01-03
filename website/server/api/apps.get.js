// server/api/apps.get.js
export default defineEventHandler(async (event) => {
  // In a real implementation, this would fetch data from apps.yaml or a database
  // For now, returning sample data
  const apps = [
    { id: 1, name: 'PojavLauncher', author: 'PojavLauncherTeam', category: 'Gaming', domain: 'Minecraft', description: 'Minecraft: Java Edition for Android', status: 'Discontinued', url: 'https://github.com/PojavLauncherTeam/PojavLauncher' },
    { id: 2, name: 'Zalith Launcher', author: 'ZalithLauncher', category: 'Gaming', domain: 'Minecraft', description: 'Minecraft launcher for Android', status: 'Stable', url: 'https://github.com/ZalithLauncher/ZalithLauncher' },
    { id: 3, name: 'Termux:Monet', author: 'FlutterGenerator', category: 'Terminal', domain: 'Development', description: 'Terminal emulator with Material You design', status: 'Stable', url: 'https://github.com/FlutterGenerator/termux-monet' },
    { id: 4, name: 'Termux:API', author: 'termux', category: 'Terminal', domain: 'Development', description: 'API access for Termux', status: 'Stable', url: 'https://github.com/termux/termux-api' },
    { id: 5, name: 'Neo Store', author: 'NeoApplications', category: 'AppStore', domain: 'System', description: 'F-Droid client with modern UI', status: 'Stable', url: 'https://github.com/NeoApplications/Neo-Store' },
    { id: 6, name: 'CloudStream', author: 'recloudstream', category: 'Media Player', domain: 'Entertainment', description: 'Movie and TV show streaming', status: 'Stable', url: 'https://github.com/recloudstream/cloudstream' },
    { id: 7, name: 'Mihon', author: 'mihonapp', category: 'Manga Reader', domain: 'Entertainment', description: 'Tachiyomi fork with modern features', status: 'Stable', url: 'https://github.com/mihonapp/mihon' },
    { id: 8, name: 'Signal', author: 'Signal Foundation', category: 'Messaging', domain: 'Communication', description: 'Private messaging application', status: 'Stable', url: 'https://github.com/signalapp/Signal-Android' },
  ]

  return {
    apps,
    total: apps.length,
    categories: [...new Set(apps.map(app => app.category))],
    domains: [...new Set(apps.map(app => app.domain))]
  }
})