<script setup lang="ts">
/**
 * 音乐库管理主页
 *
 * 职责:
 * 1. 展示分页的音乐列表数据。
 * 2. 提供“上传音乐”入口（仅管理员可见）。
 * 3. 协调 UploadModal 组件。
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
  NPopconfirm,
  type DataTableColumns
} from 'naive-ui';
import {CloudUploadOutline as UploadIcon, Refresh as RefreshIcon, Play as PlayIcon} from '@vicons/ionicons5';
import {musicApi} from '@/api/music';
import {useUserStore} from '@/stores/userStore';
import {usePlayerStore} from '@/stores/playerStore';
import type {Music} from '@/types/entity';
import UploadModal from './UploadModal.vue';

// --- State ---
const userStore = useUserStore();
const playerStore = usePlayerStore();
const message = useMessage();

const loading = ref(false);
const showUploadModal = ref(false);
const musicList = ref<Music[]>([]);

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0, // 后端目前列表接口可能没返回总数，这里暂且保留
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

/**
 * 表格列定义
 * @design
 * 使用 render 函数处理嵌套数据的展示 (如 album.title, album.artist.name)。
 * 这种方式比 slot 更具类型安全性。
 */

// 删除处理函数
const handleDelete = async (id: number) => {
  try {
    await musicApi.deleteMusic(id);
    message.success('删除成功');
    // 刷新列表
    loadData();
  } catch (error) {
    // 错误已由拦截器处理
  }
};

// 播放处理函数
const handlePlay = (track: Music) => {
  playerStore.playTrack(track);
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
    key: 'artist', // 虚拟 Key
    width: 150,
    render(row) {
      // 嵌套结构: Music -> Album -> Artist
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
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render(row) {
      if (!row.created_at) return '-';
      const date = new Date(row.created_at);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  },

  // [新增] 操作列
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render(row) {
      const buttons = [];

      // 播放按钮 - 所有用户可见
      buttons.push(
          h(NButton, {
            size: 'small',
            type: 'primary',
            quaternary: true,
            onClick: () => handlePlay(row)
          }, {
            icon: () => h(NIcon, null, {default: () => h(PlayIcon)}),
            default: () => '播放'
          })
      );

      // 权限控制：仅管理员显示删除按钮
      if (userStore.isAdmin) {
        buttons.push(
            h(
                NPopconfirm,
                {
                  onPositiveClick: () => handleDelete(row.id)
                },
                {
                  trigger: () => h(NButton, {size: 'small', type: 'error', quaternary: true}, {default: () => '删除'}),
                  default: () => '确定要删除这首歌吗？物理文件也将被清除。'
                }
            )
        );
      }

      return h(NSpace, null, {default: () => buttons});
    }
  }

];

// --- Logic: API Calls ---

/**
 * 加载音乐数据
 * @description 根据当前分页参数计算 skip/limit 并请求后端
 */
const loadData = async () => {
  loading.value = true;
  try {
    const skip = (pagination.page - 1) * pagination.pageSize;
    const limit = pagination.pageSize;

    // 后端返回 { items: [], total: number } 格式
    const data = await musicApi.getMusicList(skip, limit);
    musicList.value = data.items;
    pagination.itemCount = data.total;
  } catch (error) {
    message.error('获取音乐列表失败');
  } finally {
    loading.value = false;
  }
};

const handleUploadSuccess = () => {
  // 上传成功后刷新列表，重置到第一页
  pagination.page = 1;
  loadData();
};

onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="library-container">
    <n-card title="音乐库管理" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-button @click="loadData" :loading="loading" quaternary circle>
            <template #icon>
              <n-icon>
                <RefreshIcon/>
              </n-icon>
            </template>
          </n-button>

          <n-button v-if="userStore.isAdmin" type="primary" @click="showUploadModal = true">
            <template #icon>
              <n-icon>
                <UploadIcon/>
              </n-icon>
            </template>
            上传音乐
          </n-button>
        </n-space>
      </template>

      <n-data-table
          remote
          :columns="columns"
          :data="musicList"
          :loading="loading"
          :pagination="pagination"
          :single-line="false"
      />
    </n-card>

    <upload-modal
        v-model:show="showUploadModal"
        @success="handleUploadSuccess"
    />
  </div>
</template>

<style scoped>
.library-container {
  /* 可以在这里添加容器特定的样式，例如最大宽度限制等 */
}
</style>