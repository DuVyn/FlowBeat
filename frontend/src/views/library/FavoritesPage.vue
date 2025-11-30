<script setup lang="ts">
/**
 * 收藏歌曲页面
 *
 * 功能:
 * 1. 展示用户收藏的所有歌曲
 * 2. 支持播放和取消收藏
 */
import {h, onMounted, ref, reactive} from 'vue';
import {
  NCard,
  NDataTable,
  NButton,
  NSpace,
  NTag,
  NIcon,
  useMessage,
  NEmpty,
  type DataTableColumns
} from 'naive-ui';
import {Refresh as RefreshIcon, Play as PlayIcon, HeartDislike as UnlikeIcon} from '@vicons/ionicons5';
import {musicApi} from '@/api/music';
import {usePlayerStore} from '@/stores/playerStore';
import type {Music} from '@/types/entity';

// --- State ---
const playerStore = usePlayerStore();
const message = useMessage();

const loading = ref(false);
const musicList = ref<Music[]>([]);

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  onChange: (page: number) => {
    pagination.page = page;
    loadData();
  }
});

// --- Logic: Data Rendering ---

/**
 * 格式化时长 (秒 -> mm:ss)
 */
const formatDuration = (seconds: number) => {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
};

// 取消收藏处理函数
const handleUnlike = async (id: number) => {
  try {
    await musicApi.removeLike(id);
    message.success('已取消收藏');
    // 刷新列表
    loadData();
  } catch (error) {
    message.error('取消收藏失败');
  }
};

// 播放处理函数 - 将所有收藏的歌曲添加到播放列表
const handlePlay = (track: Music) => {
  const startIndex = musicList.value.findIndex(m => m.id === track.id);
  playerStore.setPlaylist(musicList.value, startIndex >= 0 ? startIndex : 0);
};

const columns: DataTableColumns<Music> = [
  {
    title: 'ID',
    key: 'id',
    width: 60
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
    width: 100,
    render(row) {
      return formatDuration(row.duration);
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render(row) {
      return h(NSpace, null, {
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
            onClick: () => handleUnlike(row.id)
          }, {
            icon: () => h(NIcon, null, {default: () => h(UnlikeIcon)}),
            default: () => '取消收藏'
          })
        ]
      });
    }
  }
];

// --- Logic: API Calls ---

/**
 * 加载收藏数据
 */
const loadData = async () => {
  loading.value = true;
  try {
    const skip = (pagination.page - 1) * pagination.pageSize;
    const limit = pagination.pageSize;

    const data = await musicApi.getLikedMusic(skip, limit);
    musicList.value = data.items;
    pagination.itemCount = data.total;
  } catch (error) {
    message.error('获取收藏列表失败');
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="favorites-container">
    <n-card title="我的收藏" :bordered="false">
      <template #header-extra>
        <n-button @click="loadData" :loading="loading" quaternary circle>
          <template #icon>
            <n-icon>
              <RefreshIcon/>
            </n-icon>
          </template>
        </n-button>
      </template>

      <n-empty v-if="!loading && musicList.length === 0" description="暂无收藏的歌曲">
        <template #extra>
          <n-button size="small" @click="$router.push('/library')">
            去音乐库看看
          </n-button>
        </template>
      </n-empty>

      <n-data-table
          v-else
          remote
          :columns="columns"
          :data="musicList"
          :loading="loading"
          :pagination="pagination"
          :single-line="false"
      />
    </n-card>
  </div>
</template>

<style scoped>
.favorites-container {
  /* 可以在这里添加容器特定的样式 */
}
</style>