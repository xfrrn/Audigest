<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import api from '@/api'
import { useRouter } from 'vue-router'
import { Loader2, CheckCircle2, Clock, AlertCircle, FileText, RefreshCw, Plus } from 'lucide-vue-next'

const router = useRouter()

const { data: mediaList, isLoading, refetch, isRefetching } = useQuery({
  queryKey: ['mediaList'],
  queryFn: () => api.getMediaList(),
  refetchInterval: (query) => {
    const data = query.state.data
    if (!data) return 3000
    const hasPending = data.some((item: any) => 
      ['pending', 'processing'].includes(item.status)
    )
    return hasPending ? 3000 : false
  }
})

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed': return 'bg-green-100 text-green-800 border-green-200'
    case 'failed': return 'bg-red-100 text-red-800 border-red-200'
    default: return 'bg-yellow-100 text-yellow-800 border-yellow-200'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed': return CheckCircle2
    case 'failed': return AlertCircle
    default: return Clock
  }
}

const formatStatus = (status: string) => {
  return status.charAt(0).toUpperCase() + status.slice(1);
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 p-4 sm:p-8">
    <div class="max-w-6xl mx-auto">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
        <div>
          <h1 class="text-3xl font-bold text-gray-900 tracking-tight">Dashboard</h1>
          <p class="text-gray-500 mt-1">Manage your video summaries and transcripts.</p>
        </div>
        <div class="flex gap-3">
          <button 
            @click="() => refetch()" 
            class="p-2 bg-white border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition-colors"
            :class="{ 'animate-spin': isRefetching }"
            title="Refresh"
          >
            <RefreshCw class="h-5 w-5" />
          </button>
          <button 
            @click="router.push('/')" 
            class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 shadow-sm flex items-center gap-2 transition-all hover:shadow-md"
          >
            <Plus class="h-4 w-4" />
            New Task
          </button>
        </div>
      </div>

      <div v-if="isLoading" class="flex justify-center py-24">
        <Loader2 class="h-10 w-10 animate-spin text-blue-600" />
      </div>

      <div v-else-if="!mediaList || mediaList.length === 0" class="text-center py-24 bg-white rounded-2xl border border-dashed border-gray-300">
        <div class="bg-gray-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
          <FileText class="h-8 w-8 text-gray-400" />
        </div>
        <h3 class="text-lg font-medium text-gray-900">No tasks yet</h3>
        <p class="text-gray-500 mt-1 mb-6">Start by submitting a video URL.</p>
        <button 
          @click="router.push('/')" 
          class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 shadow-sm inline-flex items-center gap-2"
        >
          <Plus class="h-4 w-4" />
          Create First Task
        </button>
      </div>

      <div v-else class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div
          v-for="item in mediaList"
          :key="item.id"
          @click="router.push(`/media/${item.id}`)"
          class="bg-white p-6 rounded-xl shadow-sm border border-gray-200 hover:shadow-lg hover:border-blue-200 transition-all cursor-pointer group relative overflow-hidden"
        >
          <div class="absolute top-0 left-0 w-1 h-full" :class="{
            'bg-green-500': item.status === 'completed',
            'bg-yellow-500': ['pending', 'processing'].includes(item.status),
            'bg-red-500': item.status === 'failed'
          }"></div>

          <div class="flex justify-between items-start mb-4 pl-2">
            <div class="p-2 bg-gray-50 rounded-lg text-gray-500 group-hover:bg-blue-50 group-hover:text-blue-600 transition-colors">
              <FileText class="h-6 w-6" />
            </div>
            <span
              class="px-2.5 py-0.5 rounded-full text-xs font-medium border flex items-center gap-1.5"
              :class="getStatusColor(item.status)"
            >
              <component :is="getStatusIcon(item.status)" class="h-3.5 w-3.5" />
              {{ formatStatus(item.status) }}
            </span>
          </div>
          
          <div class="pl-2">
            <h3 class="font-semibold text-gray-900 mb-2 line-clamp-2 group-hover:text-blue-600 transition-colors text-lg leading-snug">
              {{ item.title || item.original_url }}
            </h3>
            
            <div class="flex items-center gap-4 text-xs text-gray-500 mt-6">
              <span class="bg-gray-100 px-2 py-1 rounded text-gray-600 font-medium">{{ item.platform }}</span>
              <span>{{ new Date(item.created_at).toLocaleDateString() }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
