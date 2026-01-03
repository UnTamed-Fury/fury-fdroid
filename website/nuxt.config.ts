export default defineNuxtConfig({
  devtools: { enabled: true },
  css: ['~/assets/css/main.css'],
  app: {
    head: {
      charset: 'utf-8',
      viewport: 'width=device-width, initial-scale=1',
      title: 'Fury\'s F-Droid Repo',
      meta: [
        { name: 'description', content: 'Custom F-Droid repository for open-source Android apps.' }
      ]
    }
  }
})