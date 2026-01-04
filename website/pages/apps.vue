<template>
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-8 text-center">All Apps</h1>
    
    <div class="mb-8">
      <input 
        v-model="searchQuery" 
        type="text" 
        placeholder="Search apps..." 
        class="w-full max-w-md mx-auto block p-3 rounded-lg bg-space-950 border border-border text-white"
      />
    </div>
    
    <div class="app-grid">
      <div 
        v-for="app in filteredApps" 
        :key="app.id" 
        class="app-card hover:transform hover:translate-y-[-5px] transition-all duration-300"
      >
        <div class="flex items-center">
          <div class="bg-gray-200 border-2 border-dashed rounded-xl w-16 h-16" />
          <div class="ml-4">
            <h3 class="app-name text-lg font-semibold">{{ app.name }}</h3>
            <p class="app-author text-sm">by {{ app.author }}</p>
            <div class="mt-2">
              <span class="app-category mr-2">{{ app.category }}</span>
              <span class="app-category">{{ app.domain }}</span>
            </div>
          </div>
        </div>
        <div class="mt-4">
          <p class="text-sm text-text-muted">{{ app.description }}</p>
        </div>
      </div>
    </div>
    
    <div v-if="filteredApps.length === 0" class="text-center py-12">
      <p class="text-text-muted">No apps found matching your search.</p>
    </div>
  </div>
</template>

<script setup>
const searchQuery = ref('')

// Fetch apps from API
const { data: appsData } = await useFetch('/api/apps')
const allApps = appsData?.value?.apps || []

const filteredApps = computed(() => {
  if (!searchQuery.value) return allApps

  const query = searchQuery.value.toLowerCase()
  return allApps.filter(app =>
    app.name.toLowerCase().includes(query) ||
    app.author.toLowerCase().includes(query) ||
    app.category.toLowerCase().includes(query) ||
    app.domain.toLowerCase().includes(query) ||
    app.description.toLowerCase().includes(query)
  )
})
</script>