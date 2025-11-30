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
import {CloudUploadOutline as UploadIcon, Refresh as RefreshIcon} from '@vicons/ionicons5';
import {musicApi} from '@/api/music';
import {useUserStore} from '@/stores/userStore';
import type {Music} from '@/types/entity';
import UploadModal from './UploadModal.vue';

// --- State ---
const userStore = useUserStore();
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
    key: 'created_at', // 假设后端后续会返回
    width: 180,
    render(_) {
      // 若后端模型中没有 exposed created_at，这里可能需要调整
      // 目前 types/entity.ts 中未定义 created_at，暂不渲染或预留
      return '-';
    }
  },

  // [新增] 操作列
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render(row) {
      // 权限控制：仅管理员显示删除按钮
      if (!userStore.isAdmin) return null;

      return h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete(row.id)
          },
          {
            trigger: () => h(NButton, {size: 'small', type: 'error', quaternary: true}, {default: () => '删除'}),
            default: () => '确定要删除这首歌吗？物理文件也将被清除。'
          }
      );
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

    // 注意：当前 musicApi.getMusicList 返回的是 Music[] 数组，
    // 如果后端支持总数返回 (e.g. { items: [], total: 100 })，分页体验会更好。
    // 目前基于提供的后端代码，只能获取列表。
    const data = await musicApi.getMusicList(skip, limit);
    musicList.value = data;

    // 临时处理：如果返回的数据量少于 limit，说明到底了，或者后端暂未提供 count 接口
    // 实际生产环境建议后端增加 /music/count 接口或在 list 接口返回总数
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