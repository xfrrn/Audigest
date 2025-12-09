<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMutation } from '@tanstack/vue-query'
import api from '@/api'
import { Loader2, Youtube, Tv, LayoutDashboard } from 'lucide-vue-next'

const url = ref('')
const router = useRouter()

const { mutate, isPending } = useMutation({
  mutationFn: api.createMediaTask,
  onSuccess: () => {
    router.push('/dashboard')
  },
  onError: (error) => {
    console.error(error)
    alert('Failed to submit task. Please check the URL and try again.')
  }
})

const handleSubmit = () => {
  if (!url.value) return
  mutate(url.value)
}
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-gray-50 to-gray-100 text-gray-900 p-4 relative overflow-hidden">
    <!-- Background decoration -->
    <div class="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
      <div class="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-blue-200/20 blur-3xl"></div>
      <div class="absolute top-[40%] -right-[10%] w-[40%] h-[40%] rounded-full bg-cyan-200/20 blur-3xl"></div>
    </div>

    <div class="w-full max-w-3xl space-y-10 text-center z-10">
      <div class="space-y-4">
        <h1 class="text-6xl font-black tracking-tighter sm:text-8xl bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-500 bg-clip-text text-transparent drop-shadow-sm">
          Audigest
        </h1>
        <p class="text-xl sm:text-2xl text-gray-600 font-light max-w-2xl mx-auto">
          Transform long videos into concise summaries and searchable transcripts with AI.
        </p>
      </div>

      <div class="bg-white p-2 rounded-2xl shadow-xl border border-gray-100 flex flex-col sm:flex-row gap-2 transition-all hover:shadow-2xl">
        <input
          v-model="url"
          type="text"
          placeholder="Paste YouTube or Bilibili URL here..."
          class="flex-1 h-14 px-6 rounded-xl bg-transparent focus:outline-none text-lg placeholder:text-gray-400"
          @keyup.enter="handleSubmit"
        />
        <button
          @click="handleSubmit"
          :disabled="isPending || !url"
          class="h-14 px-8 rounded-xl bg-blue-600 text-white hover:bg-blue-700 inline-flex items-center justify-center font-semibold text-lg transition-all shadow-md disabled:opacity-70 disabled:cursor-not-allowed hover:scale-[1.02] active:scale-[0.98]"
        >
          <Loader2 v-if="isPending" class="mr-2 h-5 w-5 animate-spin" />
          {{ isPending ? 'Processing...' : 'Digest Video' }}
        </button>
      </div>

      <div class="pt-8 flex justify-center gap-12 text-gray-400 grayscale hover:grayscale-0 transition-all duration-500">
        <div class="flex flex-col items-center gap-2 group cursor-default">
          <Youtube class="h-8 w-8 group-hover:text-red-600 transition-colors" />
          <span class="text-xs font-medium group-hover:text-gray-600">YouTube</span>
        </div>
        <div class="flex flex-col items-center gap-2 group cursor-default">
          <Tv class="h-8 w-8 group-hover:text-blue-400 transition-colors" />
          <span class="text-xs font-medium group-hover:text-gray-600">Bilibili</span>
        </div>
      </div>
      
      <div class="pt-4">
        <router-link to="/dashboard" class="inline-flex items-center text-gray-500 hover:text-blue-600 transition-colors text-sm font-medium">
          <LayoutDashboard class="w-4 h-4 mr-2" />
          Go to Dashboard
        </router-link>
      </div>
    </div>
  </div>
</template>
