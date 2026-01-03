<template>
  <div class="container mx-auto px-4 py-8 max-w-4xl">
    <h1 class="text-3xl font-bold mb-8 text-center">About Fury's F-Droid Repository</h1>
    
    <section class="card mb-8">
      <h2 class="text-2xl font-bold mb-4">What is this repository?</h2>
      <p class="mb-4">
        Fury's F-Droid Repository is a high-performance, automated F-Droid repository hosting a curated collection of open-source Android apps. 
        This repository is stateless and fully automated, fetching updates, metadata, and icons directly from GitHub Releases.
      </p>
      
      <p class="mb-4">
        Our goal is to provide a reliable source for open-source Android applications with clean, normalized metadata and optimized performance.
      </p>
    </section>
    
    <section class="card mb-8">
      <h2 class="text-2xl font-bold mb-4">Features</h2>
      <ul class="list-disc pl-6 space-y-2">
        <li><strong>Automated Updates:</strong> Checks for new releases every 6 hours via GitHub Actions</li>
        <li><strong>Stateless Architecture:</strong> APKs are not stored in git history, keeping the repository size small and builds fast</li>
        <li><strong>Smart Metadata:</strong> Automatically fetches app descriptions and icons from upstream GitHub repositories</li>
        <li><strong>Optimized Icons:</strong> Automatically converts and optimizes app icons for F-Droid compatibility</li>
        <li><strong>Version Control:</strong> Maintains the latest 2 versions of each app to save bandwidth and storage</li>
      </ul>
    </section>
    
    <section class="card mb-8">
      <h2 class="text-2xl font-bold mb-4">How it Works</h2>
      <div class="steps">
        <div class="step">
          <h3 class="text-accent">1. Source of Truth</h3>
          <p>apps.yaml defines the list of apps and their metadata</p>
        </div>
        <div class="step">
          <h3>2. Watcher Phase</h3>
          <p>Scheduled workflow checks GitHub for new releases of tracked apps</p>
        </div>
        <div class="step">
          <h3>3. Setup Phase</h3>
          <p>Prepares directory structure and fetches/updates icons</p>
        </div>
        <div class="step">
          <h3>4. Download Phase</h3>
          <p>Downloads APKs from GitHub Releases and passes them as artifacts</p>
        </div>
        <div class="step">
          <h3>5. Index Phase</h3>
          <p>Generates the F-Droid repository index with APKs from artifacts</p>
        </div>
        <div class="step">
          <h3>6. Deploy Phase</h3>
          <p>Publishes the static website and repository to GitHub Pages</p>
        </div>
      </div>
    </section>
    
    <section class="card">
      <h2 class="text-2xl font-bold mb-4">Security Notice</h2>
      <p>
        This repository uses a secure keystore for signing the F-Droid repository. 
        The repository fingerprint uses 4096-bit RSA encryption for enhanced security. 
        All applications in this repository are open-source and verified.
      </p>
    </section>
  </div>
</template>