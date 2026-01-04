<template>
  <div>
    <nav class="navbar border-b border-border py-4">
      <div class="container mx-auto flex justify-between items-center">
        <NuxtLink to="/" class="text-2xl font-bold text-white">Fury's F-Droid</NuxtLink>
        <div class="nav-links">
          <NuxtLink to="/" class="nav-link">Home</NuxtLink>
          <NuxtLink to="/apps" class="nav-link">Apps</NuxtLink>
          <NuxtLink to="/about" class="nav-link">About</NuxtLink>
        </div>
      </div>
    </nav>
    
    <slot />
  </div>
</template>

<style scoped>
.navbar {
  border-bottom: 1px solid var(--border);
  padding: 1rem 0;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-link {
  color: var(--white);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.nav-link:hover,
.nav-link.nuxt-link-exact-active {
  color: var(--accent);
}
</style>