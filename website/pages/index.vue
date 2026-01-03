<template>
  <div>
    <header class="text-center py-12">
      <h1 class="text-3xl md:text-5xl font-bold mb-4">Fury's F-Droid Repo</h1>
      <p class="text-lg text-text-muted max-w-2xl mx-auto">
        Open-source Android apps distributed through a custom F-Droid repository.
      </p>
    </header>

    <main class="max-w-4xl mx-auto px-4">
      <section class="card mb-8">
        <h2 class="text-2xl font-bold mb-4">Repository URL</h2>
        <p class="mb-6">Add this URL inside the F-Droid client.</p>

        <div class="field-row mb-6">
          <input 
            id="repo" 
            :value="repoUrl" 
            readonly 
            class="w-full"
          />
          <button @click="copyToClipboard('repo')" class="flex-shrink-0">
            Copy
          </button>
          <span class="tag">URL</span>
        </div>

        <div class="qr text-center my-8">
          <img 
            src="/qr.png" 
            alt="F-Droid repository QR code" 
            class="mx-auto max-w-xs rounded-lg border-4 border-white"
          />
        </div>

        <h3 class="text-xl font-bold mb-2">Repository Fingerprint</h3>
        <p class="text-text-muted mb-4">Standard F-Droid format.</p>

        <div class="field-row mb-4">
          <input 
            id="fp-colon" 
            :value="fingerprint" 
            readonly 
          />
          <button @click="copyToClipboard('fp-colon')">Copy</button>
          <span class="tag">SHA-256</span>
        </div>

        <h3 class="text-xl font-bold mt-6 mb-2">Neo Store Compatible Fingerprint</h3>
        <p class="text-text-muted mb-4">Same fingerprint without separators.</p>

        <div class="field-row">
          <input 
            id="fp-raw" 
            :value="fingerprint.replace(/:/g, '')" 
            readonly 
          />
          <button @click="copyToClipboard('fp-raw')">Copy</button>
          <span class="tag">RAW</span>
        </div>

        <div class="steps mt-8">
          <div class="step">
            <h3 class="text-accent">1. Install an F-Droid client</h3>
            <p>
              You can use the official F-Droid app or any compatible client.
              Recommended: <strong>F-Droid (official)</strong> or <strong>Neo Store</strong>.
            </p>
          </div>
          <div class="step">
            <h3>2. Add Repository</h3>
            <p>Settings → Repositories → Add.</p>
          </div>
          <div class="step">
            <h3>3. Refresh</h3>
            <p>Update indexes and install apps.</p>
          </div>
        </div>
      </section>

      <!-- Repository Stats Section -->
      <section class="card mb-8">
        <h2 class="text-2xl font-bold mb-6">Repository Statistics</h2>
        <div class="stats-grid">
          <div class="stat-card">
            <span class="stat-number">{{ appCount }}</span>
            <span class="stat-label">Apps</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ categoryCount }}</span>
            <span class="stat-label">Categories</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ updateFrequency }}</span>
            <span class="stat-label">Update Frequency</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ repoSize }}</span>
            <span class="stat-label">Repository Size</span>
          </div>
        </div>
      </section>

      <!-- Featured Apps Section -->
      <section class="card">
        <h2 class="text-2xl font-bold mb-6">Featured Apps</h2>
        <div class="app-grid">
          <div 
            v-for="app in featuredApps" 
            :key="app.id" 
            class="app-card"
          >
            <div class="flex items-center">
              <div class="bg-gray-200 border-2 border-dashed rounded-xl w-16 h-16" />
              <div class="ml-4">
                <h3 class="app-name">{{ app.name }}</h3>
                <p class="app-author">by {{ app.author }}</p>
                <span class="app-category">{{ app.category }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <footer class="text-center py-8 text-text-muted text-sm">
      © 2025 · 
      <a 
        href="https://github.com/UnTamed-Fury/fury-fdroid" 
        class="text-white hover:text-accent transition-colors"
      >
        Fury's F-Droid Repository
      </a> · Open Source
    </footer>
  </div>
</template>

<script setup>
const repoUrl = 'https://fury.untamedfury.space/repo'
const fingerprint = 'BD:3D:60:C7:D6:AA:34:20:42:78:62:9B:0F:BC:EC:E7:B6:80:2E:6B:C6:7C:5F:11:12:D2:60:D4:21:86:EE:E6'

// Fetch repository stats
const { data: stats } = await useFetch('/api/stats')
const { data: appsData } = await useFetch('/api/apps')

const appCount = stats?.value?.totalApps || 0
const categoryCount = stats?.value?.totalCategories || 0
const updateFrequency = stats?.value?.updateFrequency || 'Every 6 hours'
const repoSize = stats?.value?.repoSize || 'Stateless'

// Get featured apps from the API response
const featuredApps = appsData?.value?.apps?.slice(0, 6) || [
  { id: 1, name: 'PojavLauncher', author: 'PojavLauncherTeam', category: 'Gaming' },
  { id: 2, name: 'Termux', author: 'termux', category: 'Development' },
  { id: 3, name: 'Neo Store', author: 'NeoApplications', category: 'AppStore' },
  { id: 4, name: 'CloudStream', author: 'recloudstream', category: 'Entertainment' },
  { id: 5, name: 'Mihon', author: 'mihonapp', category: 'Manga Reader' },
  { id: 6, name: 'Signal', author: 'Signal Foundation', category: 'Messaging' }
]

const copyToClipboard = (elementId) => {
  const element = document.getElementById(elementId)
  if (element) {
    element.select()
    navigator.clipboard.writeText(element.value)
    // Optional: Show a visual feedback
    const button = element.nextElementSibling
    if (button) {
      const originalText = button.textContent
      button.textContent = 'Copied!'
      setTimeout(() => {
        button.textContent = originalText
      }, 2000)
    }
  }
}
</script>