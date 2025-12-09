<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuery } from '@tanstack/vue-query'
import api from '@/api'
import MarkdownIt from 'markdown-it'
import { Loader2, ArrowLeft, FileText, AlignLeft, ExternalLink, Play } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const md = new MarkdownIt()

const mediaId = Number(route.params.id)
const activeTab = ref<'transcript' | 'summary'>('summary')
const currentSeekTime = ref(0)

// Fetch Media Details
const { data: media, isLoading: isMediaLoading } = useQuery({
  queryKey: ['media', mediaId],
  queryFn: () => api.getMediaDetail(mediaId)
})

// Fetch Transcript
const { data: transcript, isLoading: isTranscriptLoading } = useQuery({
  queryKey: ['transcript', mediaId],
  queryFn: () => api.getMediaTranscript(mediaId),
  enabled: computed(() => media.value?.status === 'completed')
})

// Fetch Summary
const { data: summary, isLoading: isSummaryLoading } = useQuery({
  queryKey: ['summary', mediaId],
  queryFn: async () => {
    try {
      // @ts-ignore
      const res = await api.getMediaSummary(mediaId)
      return res
    } catch (e) {
      return null
    }
  },
  enabled: computed(() => media.value?.status === 'completed')
})

const embedUrl = computed(() => {
  if (!media.value) return ''
  const url = media.value.original_url
  
  if (url.includes('youtube.com') || url.includes('youtu.be')) {
    let videoId = ''
    if (url.includes('v=')) {
      const parts = url.split('v=')
      if (parts.length > 1 && parts[1]) {
        const subParts = parts[1].split('&')
        if (subParts.length > 0 && subParts[0]) {
          videoId = subParts[0]
        }
      }
    } else if (url.includes('youtu.be/')) {
      const parts = url.split('youtu.be/')
      if (parts.length > 1 && parts[1]) {
        const subParts = parts[1].split('?')
        if (subParts.length > 0 && subParts[0]) {
          videoId = subParts[0]
        }
      }
    }
    if (videoId) {
      return `https://www.youtube.com/embed/${videoId}?autoplay=1&start=${Math.floor(currentSeekTime.value)}`
    }
  }
  
  if (url.includes('bilibili.com')) {
    // Extract BVID
    const match = url.match(/video\/(BV\w+)/)
    if (match) {
      return `https://player.bilibili.com/player.html?bvid=${match[1]}&t=${Math.floor(currentSeekTime.value)}&high_quality=1`
    }
  }
  
  return ''
})

const handleSeek = (time: number) => {
  currentSeekTime.value = time
}

const formatTime = (seconds: number) => {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex flex-col h-screen">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-4 shrink-0 z-10">
      <button 
        @click="router.push('/dashboard')" 
        class="p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-500"
      >
        <ArrowLeft class="h-5 w-5" />
      </button>
      <div class="flex-1 min-w-0">
        <h1 class="text-lg font-semibold text-gray-900 truncate">
          {{ media?.title || 'Loading...' }}
        </h1>
        <div class="flex items-center gap-2 text-xs text-gray-500">
          <span v-if="media?.platform" class="capitalize">{{ media.platform }}</span>
          <span v-if="media?.created_at">• {{ new Date(media.created_at).toLocaleDateString() }}</span>
          <a v-if="media?.original_url" :href="media.original_url" target="_blank" class="flex items-center gap-1 hover:text-blue-600">
            Original Link <ExternalLink class="h-3 w-3" />
          </a>
        </div>
      </div>
      <div class="flex gap-2">
        <button 
          @click="activeTab = 'summary'"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          :class="activeTab === 'summary' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100'"
        >
          <AlignLeft class="h-4 w-4" />
          Summary
        </button>
        <button 
          @click="activeTab = 'transcript'"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          :class="activeTab === 'transcript' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100'"
        >
          <FileText class="h-4 w-4" />
          Transcript
        </button>
      </div>
    </header>

    <!-- Content -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Left: Video Player -->
      <div class="w-1/2 bg-black flex items-center justify-center relative group">
        <iframe
          v-if="embedUrl"
          :src="embedUrl"
          class="w-full h-full"
          frameborder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen
        ></iframe>
        <div v-else class="text-white text-center p-8">
          <p class="mb-4">Video preview not available for this URL.</p>
          <a 
            v-if="media?.original_url" 
            :href="media.original_url" 
            target="_blank"
            class="inline-flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
          >
            Open Original <ExternalLink class="h-4 w-4" />
          </a>
        </div>
      </div>

      <!-- Right: Transcript / Summary -->
      <div class="w-1/2 bg-white border-l border-gray-200 overflow-y-auto custom-scrollbar">
        
        <!-- Loading State -->
        <div v-if="isMediaLoading || (activeTab === 'transcript' && isTranscriptLoading) || (activeTab === 'summary' && isSummaryLoading)" class="flex flex-col items-center justify-center h-full text-gray-400">
          <Loader2 class="h-8 w-8 animate-spin mb-2" />
          <p>Loading content...</p>
        </div>

        <!-- Summary Tab -->
        <div v-else-if="activeTab === 'summary'" class="p-8 max-w-3xl mx-auto">
          <div v-if="summary && summary.summaries && summary.summaries.length > 0">
            <div v-for="(item, idx) in summary.summaries" :key="idx" class="mb-8">
              <div class="prose prose-blue max-w-none" v-html="md.render(item.content)"></div>
              <div class="mt-4 flex flex-wrap gap-2">
                <span v-for="tag in item.tags" :key="tag" class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                  #{{ tag }}
                </span>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-12 text-gray-500">
            <AlignLeft class="h-12 w-12 mx-auto mb-3 opacity-20" />
            <p>No summary available yet.</p>
          </div>
        </div>

        <!-- Transcript Tab -->
        <div v-else-if="activeTab === 'transcript'" class="divide-y divide-gray-100">
          <div v-if="transcript && transcript.segments && transcript.segments.length > 0">
            <div 
              v-for="(segment, idx) in transcript.segments" 
              :key="idx"
              class="p-4 hover:bg-blue-50 transition-colors cursor-pointer group flex gap-4"
              @click="handleSeek(segment.start_time)"
            >
              <div class="shrink-0 w-16 pt-1">
                <span class="text-xs font-mono text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded group-hover:bg-blue-100">
                  {{ formatTime(segment.start_time) }}
                </span>
              </div>
              <div class="flex-1">
                <p class="text-gray-800 leading-relaxed">{{ segment.text }}</p>
                <p v-if="segment.speaker_label" class="text-xs text-gray-400 mt-1 font-medium">
                  {{ segment.speaker_label }}
                </p>
              </div>
              <div class="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity self-center">
                <button class="p-1.5 text-blue-600 hover:bg-blue-100 rounded-full">
                  <Play class="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-12 text-gray-500">
            <FileText class="h-12 w-12 mx-auto mb-3 opacity-20" />
            <p>No transcript available yet.</p>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #e5e7eb;
  border-radius: 20px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: #d1d5db;
}
</style>

