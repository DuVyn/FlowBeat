<script setup lang="ts">
import {h, ref, watch, onMounted, type Component} from 'vue';
import {NMenu, NIcon, NDivider, NButton, NModal, NInput, NForm, NFormItem, useMessage, type MenuOption} from 'naive-ui';
import {RouterLink, useRoute, useRouter} from 'vue-router';
import {usePlaylistStore} from '@/stores/playlistStore';

import {
  Library as LibraryIcon,
  Compass as DiscoveryIcon,
  Heart as HeartIcon,
  List as PlaylistIcon,
  Add as AddIcon
} from '@vicons/ionicons5';

/**
 * 渲染图标的辅助工厂函数
 * * @param icon - Vue 组件 (Ionicons)
 * @returns 渲染函数
 * * @design
 * 使用渲染函数 (Render Function) 而非模板语法的权衡：
 * Naive UI 的 icon 属性需要一个返回 VNode 的函数。
 * 直接传递组件会导致性能损耗，封装为闭包函数可按需渲染。
 */
function renderIcon(icon: Component) {
  return () => h(NIcon, null, {default: () => h(icon)});
}

// 路由实例
const route = useRoute();
const router = useRouter();
const playlistStore = usePlaylistStore();
const message = useMessage();

/**
 * 菜单状态管理
 */
const activeKey = ref<string | null>(null);

// 新建歌单弹窗
const showCreateModal = ref(false);
const newPlaylistName = ref('');
const newPlaylistDesc = ref('');
const isCreating = ref(false);

/**
 * 菜单配置项
 */
const menuOptions: MenuOption[] = [
  {
    label: () => h(RouterLink, {to: '/discovery'}, {default: () => '发现'}),
    key: 'discovery',
    icon: renderIcon(DiscoveryIcon),
  },
  {
    label: () => h(RouterLink, {to: '/library'}, {default: () => '音乐库'}),
    key: 'library',
    icon: renderIcon(LibraryIcon),
  },
  {
    label: () => h(RouterLink, {to: '/favorites'}, {default: () => '我的收藏'}),
    key: 'favorites',
    icon: renderIcon(HeartIcon),
  },
];

/**
 * 路由同步监听
 */
watch(
    () => route.name,
    (newRouteName) => {
      if (newRouteName && typeof newRouteName === 'string') {
        activeKey.value = newRouteName;
      } else {
        activeKey.value = null;
      }
    },
    {immediate: true}
);

// 加载歌单列表
onMounted(() => {
  playlistStore.fetchPlaylists();
});

// 创建歌单
const handleCreatePlaylist = async () => {
  if (!newPlaylistName.value.trim()) {
    message.warning('请输入歌单名称');
    return;
  }
  
  isCreating.value = true;
  try {
    await playlistStore.createPlaylist(
      newPlaylistName.value.trim(),
      newPlaylistDesc.value.trim() || undefined
    );
    message.success('歌单创建成功');
    showCreateModal.value = false;
    newPlaylistName.value = '';
    newPlaylistDesc.value = '';
  } catch (error) {
    message.error('创建歌单失败');
  } finally {
    isCreating.value = false;
  }
};

// 跳转到歌单详情
const goToPlaylist = (id: number) => {
  router.push(`/playlist/${id}`);
};
</script>

<template>
  <div class="sidebar-container">
    <n-menu
        v-model:value="activeKey"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
    />
    
    <n-divider style="margin: 16px 0 8px 0" />
    
    <div class="playlist-section">
      <div class="playlist-header">
        <span class="playlist-title">我的歌单</span>
        <n-button quaternary circle size="tiny" @click="showCreateModal = true">
          <template #icon>
            <n-icon><AddIcon /></n-icon>
          </template>
        </n-button>
      </div>
      
      <div class="playlist-list">
        <div
          v-for="playlist in playlistStore.playlists"
          :key="playlist.id"
          class="playlist-item"
          @click="goToPlaylist(playlist.id)"
        >
          <n-icon :size="16"><PlaylistIcon /></n-icon>
          <span class="playlist-name">{{ playlist.name }}</span>
        </div>
        <div v-if="playlistStore.playlists.length === 0" class="empty-hint">
          暂无歌单
        </div>
      </div>
    </div>
    
    <!-- 新建歌单弹窗 -->
    <n-modal
      v-model:show="showCreateModal"
      preset="dialog"
      title="新建歌单"
      positive-text="创建"
      negative-text="取消"
      :positive-button-props="{ loading: isCreating }"
      @positive-click="handleCreatePlaylist"
    >
      <n-form>
        <n-form-item label="歌单名称" required>
          <n-input v-model:value="newPlaylistName" placeholder="请输入歌单名称" />
        </n-form-item>
        <n-form-item label="歌单描述">
          <n-input v-model:value="newPlaylistDesc" type="textarea" placeholder="可选" />
        </n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>

<style scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.playlist-section {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.playlist-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
}

.playlist-title {
  font-size: 12px;
  color: var(--n-text-color-3);
  font-weight: 500;
}

.playlist-list {
  margin-top: 4px;
}

.playlist-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.playlist-item:hover {
  background-color: var(--n-color-hover);
}

.playlist-name {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-hint {
  font-size: 12px;
  color: var(--n-text-color-3);
  text-align: center;
  padding: 16px 0;
}
</style>