<script setup lang="ts">
import {h, ref, computed, watch} from 'vue';
import {NButton, NAvatar, NDropdown, NFlex, NText, NIcon, NInput, NPopover, NSpin, NEmpty, useThemeVars} from 'naive-ui';
import {useUserStore} from '@/stores/userStore';
import {usePlayerStore} from '@/stores/playerStore';
import {useTheme} from '@/composables/useTheme';
import {LogOutOutline as LogoutIcon, Person as PersonIcon, Moon as MoonIcon, Sunny as SunIcon, Search as SearchIcon, Play as PlayIcon} from '@vicons/ionicons5';
import {useRouter} from 'vue-router';
import {musicApi} from '@/api/music';
import type {Music} from '@/types/entity';

const userStore = useUserStore();
const playerStore = usePlayerStore();
const router = useRouter();
const themeVars = useThemeVars();
const {isDark, toggleTheme} = useTheme();

// 搜索相关状态
const searchQuery = ref('');
const searchResults = ref<Music[]>([]);
const isSearching = ref(false);
const showSearchResults = ref(false);
let searchTimer: ReturnType<typeof setTimeout> | null = null;

// 用户下拉菜单选项
const userOptions = [
  {
    label: '个人资料',
    key: 'profile',
    icon: () => h(NIcon, null, {default: () => h(PersonIcon)})
  },
  {
    label: '退出登录',
    key: 'logout',
    icon: () => h(NIcon, null, {default: () => h(LogoutIcon)})
  }
];

// 处理下拉菜单点击
const handleSelect = (key: string) => {
  if (key === 'logout') {
    userStore.logout();
    router.push('/login');
  } else if (key === 'profile') {
    router.push('/profile');
  }
};

// 搜索防抖
const handleSearchInput = (value: string) => {
  searchQuery.value = value;
  
  if (searchTimer) {
    clearTimeout(searchTimer);
  }
  
  if (!value.trim()) {
    searchResults.value = [];
    showSearchResults.value = false;
    return;
  }
  
  searchTimer = setTimeout(async () => {
    await performSearch();
  }, 300);
};

// 执行搜索
const performSearch = async () => {
  if (!searchQuery.value.trim()) return;
  
  isSearching.value = true;
  showSearchResults.value = true;
  
  try {
    const response = await musicApi.searchMusic(searchQuery.value.trim());
    searchResults.value = response.items;
  } catch (error) {
    console.error('搜索失败:', error);
    searchResults.value = [];
  } finally {
    isSearching.value = false;
  }
};

// 播放搜索结果中的歌曲
const playSearchResult = (music: Music) => {
  playerStore.playTrack(music);
  showSearchResults.value = false;
  searchQuery.value = '';
  searchResults.value = [];
};

// 处理搜索框获得焦点
const handleSearchFocus = () => {
  if (searchResults.value.length > 0 || searchQuery.value.trim()) {
    showSearchResults.value = true;
  }
};

// 处理搜索框失去焦点
const handleSearchBlur = () => {
  // 延迟关闭以允许点击搜索结果
  setTimeout(() => {
    showSearchResults.value = false;
  }, 200);
};
</script>

<template>
  <div class="header-container">
    <div class="logo-area">
      <n-text class="logo-text" strong>FlowBeat</n-text>
    </div>

    <div class="search-area">
      <n-popover
        :show="showSearchResults"
        placement="bottom"
        trigger="manual"
        :show-arrow="false"
        content-style="padding: 0; width: 400px; max-height: 400px; overflow-y: auto;"
      >
        <template #trigger>
          <n-input
            v-model:value="searchQuery"
            placeholder="搜索歌曲或歌手..."
            clearable
            @input="handleSearchInput"
            @focus="handleSearchFocus"
            @blur="handleSearchBlur"
            style="width: 300px"
          >
            <template #prefix>
              <n-icon :component="SearchIcon" />
            </template>
          </n-input>
        </template>
        
        <div class="search-results">
          <n-spin v-if="isSearching" size="small" style="display: flex; justify-content: center; padding: 20px;" />
          <n-empty v-else-if="searchResults.length === 0 && searchQuery.trim()" description="未找到相关结果" />
          <div v-else class="result-list">
            <div
              v-for="item in searchResults"
              :key="item.id"
              class="result-item"
              @click="playSearchResult(item)"
            >
              <div class="result-info">
                <div class="result-title">{{ item.title }}</div>
                <div class="result-artist">{{ item.album?.artist?.name || '未知歌手' }}</div>
              </div>
              <n-button quaternary circle size="small">
                <template #icon>
                  <n-icon :component="PlayIcon" />
                </template>
              </n-button>
            </div>
          </div>
        </div>
      </n-popover>
    </div>

    <div class="actions-area">
      <n-flex align="center">
        <n-button circle quaternary @click="toggleTheme">
          <template #icon>
            <n-icon>
              <component :is="isDark ? SunIcon : MoonIcon"/>
            </n-icon>
          </template>
        </n-button>

        <n-dropdown :options="userOptions" @select="handleSelect">
          <div class="user-trigger">
            <n-avatar
                round
                size="small"
                :src="userStore.userInfo?.avatar_url || undefined"
                :fallback-src="'https://07akioni.oss-cn-beijing.aliyuncs.com/07akioni.jpeg'"
            />
            <span class="username">{{ userStore.userInfo?.username || 'User' }}</span>
          </div>
        </n-dropdown>
      </n-flex>
    </div>
  </div>
</template>

<style scoped>
.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 20px;
  border-bottom: 1px solid v-bind('themeVars.borderColor');
}

.logo-text {
  font-size: 1.2rem;
  font-weight: bold;
  background: linear-gradient(to right, #18a058, #2080f0);
  -webkit-background-clip: text;
  color: transparent;
}

.search-area {
  flex: 1;
  display: flex;
  justify-content: center;
}

.search-results {
  padding: 8px 0;
}

.result-list {
  max-height: 350px;
  overflow-y: auto;
}

.result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.result-item:hover {
  background-color: v-bind('themeVars.hoverColor');
}

.result-info {
  flex: 1;
  overflow: hidden;
}

.result-title {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-artist {
  font-size: 12px;
  color: v-bind('themeVars.textColor3');
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-trigger:hover {
  background-color: rgba(0, 0, 0, 0.05);
}
</style>