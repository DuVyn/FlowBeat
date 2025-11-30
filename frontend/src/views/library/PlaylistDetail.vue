<script setup lang="ts">
/**
 * 歌单详情页
 *
 * 功能:
 * 1. 展示歌单信息和歌曲列表
 * 2. 支持播放、编辑、删除歌曲
 */
import {h, onMounted, ref, computed} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import {
  NCard,
  NDataTable,
  NButton,
  NSpace,
  NTag,
  NIcon,
  useMessage,
  NModal,
  NInput,
  NForm,
  NFormItem,
  NPopconfirm,
  NSpin,
  NEmpty,
  type DataTableColumns
} from 'naive-ui';
import {
  Refresh as RefreshIcon,
  Play as PlayIcon,
  Trash as TrashIcon,
  Create as EditIcon
} from '@vicons/ionicons5';
import {usePlaylistStore} from '@/stores/playlistStore';
import {usePlayerStore} from '@/stores/playerStore';
import type {Music} from '@/types/entity';

// --- State ---
const route = useRoute();
const router = useRouter();
const playlistStore = usePlaylistStore();
const playerStore = usePlayerStore();
const message = useMessage();

const playlistId = computed(() => Number(route.params.id));

// 编辑弹窗
const showEditModal = ref(false);
const editName = ref('');
const editDesc = ref('');
const isUpdating = ref(false);

// --- Logic ---

/**
 * 格式化时长 (秒 -> mm:ss)
 */
const formatDuration = (seconds: number) => {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
};

// 加载歌单详情
const loadPlaylistDetail = async () => {
  await playlistStore.fetchPlaylistDetail(playlistId.value);
};

// 播放歌曲 - 将歌单中所有歌曲添加到播放列表
const handlePlay = (track: Music) => {
  if (!playlistStore.currentPlaylist) return;
  const songs = playlistStore.currentPlaylist.songs;
  const startIndex = songs.findIndex(m => m.id === track.id);
  playerStore.setPlaylist(songs, startIndex >= 0 ? startIndex : 0);
};

// 播放全部
const handlePlayAll = () => {
  if (!playlistStore.currentPlaylist?.songs.length) return;
  playerStore.setPlaylist(playlistStore.currentPlaylist.songs, 0);
};

// 从歌单移除歌曲
const handleRemoveSong = async (musicId: number) => {
  try {
    await playlistStore.removeSongFromPlaylist(playlistId.value, musicId);
    message.success('已从歌单移除');
  } catch (error) {
    message.error('移除失败');
  }
};

// 打开编辑弹窗
const openEditModal = () => {
  if (playlistStore.currentPlaylist) {
    editName.value = playlistStore.currentPlaylist.name;
    editDesc.value = playlistStore.currentPlaylist.description || '';
    showEditModal.value = true;
  }
};

// 保存编辑
const handleSaveEdit = async () => {
  if (!editName.value.trim()) {
    message.warning('歌单名称不能为空');
    return;
  }
  
  isUpdating.value = true;
  try {
    await playlistStore.updatePlaylist(
      playlistId.value,
      editName.value.trim(),
      editDesc.value.trim() || undefined
    );
    message.success('保存成功');
    showEditModal.value = false;
  } catch (error) {
    message.error('保存失败');
  } finally {
    isUpdating.value = false;
  }
};

// 删除歌单
const handleDeletePlaylist = async () => {
  try {
    await playlistStore.deletePlaylist(playlistId.value);
    message.success('歌单已删除');
    router.push('/library');
  } catch (error) {
    message.error('删除失败');
  }
};

// 表格列定义
const columns: DataTableColumns<Music> = [
  {
    title: '#',
    key: 'index',
    width: 50,
    render(_, index) {
      return index + 1;
    }
  },
  {
    title: '标题',
    key: 'title',
    width: 200,
    render(row) {
      return h('span', {style: 'font-weight: 500'}, row.title);
    }
  },
  {
    title: '艺术家',
    key: 'artist',
    width: 150,
    render(row) {
      return row.album?.artist?.name || h(NTag, {type: 'warning', size: 'small'}, {default: () => 'Unknown'});
    }
  },
  {
    title: '专辑',
    key: 'album',
    width: 150,
    render(row) {
      return row.album?.title || '-';
    }
  },
  {
    title: '时长',
    key: 'duration',
    width: 80,
    render(row) {
      return formatDuration(row.duration);
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    render(row) {
      return h(NSpace, {align: 'center'}, {
        default: () => [
          h(NButton, {
            size: 'small',
            type: 'primary',
            quaternary: true,
            onClick: () => handlePlay(row)
          }, {
            icon: () => h(NIcon, null, {default: () => h(PlayIcon)}),
            default: () => '播放'
          }),
          h(NButton, {
            size: 'small',
            type: 'error',
            quaternary: true,
            onClick: () => handleRemoveSong(row.id)
          }, {
            icon: () => h(NIcon, null, {default: () => h(TrashIcon)})
          })
        ]
      });
    }
  }
];

onMounted(() => {
  loadPlaylistDetail();
});
</script>

<template>
  <div class="playlist-detail-container">
    <n-spin :show="playlistStore.isLoading">
      <template v-if="playlistStore.currentPlaylist">
        <n-card :bordered="false">
          <template #header>
            <div class="playlist-header">
              <div class="playlist-info">
                <h2 class="playlist-name">{{ playlistStore.currentPlaylist.name }}</h2>
                <p class="playlist-desc">{{ playlistStore.currentPlaylist.description || '暂无描述' }}</p>
                <p class="playlist-meta">{{ playlistStore.currentPlaylist.song_count }} 首歌曲</p>
              </div>
            </div>
          </template>
          
          <template #header-extra>
            <n-space>
              <n-button type="primary" @click="handlePlayAll" :disabled="!playlistStore.currentPlaylist?.songs.length">
                <template #icon>
                  <n-icon><PlayIcon /></n-icon>
                </template>
                播放全部
              </n-button>
              <n-button @click="openEditModal" quaternary>
                <template #icon>
                  <n-icon><EditIcon /></n-icon>
                </template>
              </n-button>
              <n-popconfirm @positive-click="handleDeletePlaylist">
                <template #trigger>
                  <n-button quaternary type="error">
                    <template #icon>
                      <n-icon><TrashIcon /></n-icon>
                    </template>
                  </n-button>
                </template>
                确定要删除这个歌单吗？
              </n-popconfirm>
              <n-button @click="loadPlaylistDetail" quaternary circle>
                <template #icon>
                  <n-icon><RefreshIcon /></n-icon>
                </template>
              </n-button>
            </n-space>
          </template>

          <n-empty v-if="!playlistStore.currentPlaylist?.songs.length" description="歌单为空">
            <template #extra>
              <n-button size="small" @click="$router.push('/library')">
                去音乐库添加歌曲
              </n-button>
            </template>
          </n-empty>

          <n-data-table
            v-else
            :columns="columns"
            :data="playlistStore.currentPlaylist.songs"
            :single-line="false"
          />
        </n-card>
      </template>
      
      <n-empty v-else-if="!playlistStore.isLoading" description="歌单不存在" />
    </n-spin>
    
    <!-- 编辑歌单弹窗 -->
    <n-modal
      v-model:show="showEditModal"
      preset="dialog"
      title="编辑歌单"
      positive-text="保存"
      negative-text="取消"
      :positive-button-props="{ loading: isUpdating }"
      @positive-click="handleSaveEdit"
    >
      <n-form>
        <n-form-item label="歌单名称" required>
          <n-input v-model:value="editName" placeholder="请输入歌单名称" />
        </n-form-item>
        <n-form-item label="歌单描述">
          <n-input v-model:value="editDesc" type="textarea" placeholder="可选" />
        </n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>

<style scoped>
.playlist-detail-container {
  padding: 0;
}

.playlist-header {
  display: flex;
  gap: 20px;
}

.playlist-info {
  flex: 1;
}

.playlist-name {
  margin: 0 0 8px 0;
  font-size: 24px;
}

.playlist-desc {
  margin: 0 0 4px 0;
  color: var(--n-text-color-3);
  font-size: 14px;
}

.playlist-meta {
  margin: 0;
  color: var(--n-text-color-3);
  font-size: 12px;
}
</style>