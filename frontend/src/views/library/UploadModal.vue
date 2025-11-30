<script setup lang="ts">
/**
 * 音乐上传模态框组件
 *
 * 职责:
 * 1. 提供音乐文件选择与元数据录入表单。
 * 2. 处理艺术家与专辑的级联加载逻辑。
 * 3. 调用 API 执行 Multipart 文件上传。
 *
 * 交互逻辑:
 * - 只有在选择了艺术家后，才能选择专辑 (Album 依赖于 Artist)。
 * - 上传成功后抛出 'success' 事件通知父组件刷新列表。
 */
import {ref, reactive, watch} from 'vue';
import {
  NModal, NForm, NFormItem, NInput, NInputNumber,
  NSelect, NUpload, NButton, useMessage,
  type FormInst, type FormRules, type SelectOption
} from 'naive-ui';
import {musicApi} from '@/api/music';

// --- Props & Emits ---
interface Props {
  show: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits(['update:show', 'success']);

// --- State ---
const message = useMessage();
const formRef = ref<FormInst | null>(null);
const loading = ref(false);

// 级联选择器数据源
const artistOptions = ref<SelectOption[]>([]);
const albumOptions = ref<SelectOption[]>([]);
const isAlbumLoading = ref(false);

// 表单数据模型
const formModel = reactive({
  title: '',
  duration: 240, // 默认时长，后续可优化为读取文件元数据
  artist_id: null as number | null, // 辅助字段，用于筛选专辑
  album_id: null as number | null,
  track_number: 1,
});

const fileList = ref<any[]>([]);

// --- Validation Rules ---
const rules: FormRules = {
  title: {required: true, message: '请输入歌曲标题', trigger: 'blur'},
  duration: {required: true, type: 'number', message: '请输入时长', trigger: 'blur'},
  artist_id: {required: true, type: 'number', message: '请选择艺术家', trigger: ['blur', 'change']},
  album_id: {required: true, type: 'number', message: '请选择专辑', trigger: ['blur', 'change']},
};

// --- Logic: Data Fetching ---

/**
 * 获取艺术家列表
 * @description 初始化时加载，用于填充第一个下拉框
 */
const fetchArtists = async () => {
  try {
    const artists = await musicApi.getArtists();
    artistOptions.value = artists.map(a => ({
      label: a.name,
      value: a.id
    }));
  } catch (error) {
    message.error('加载艺术家列表失败');
  }
};

/**
 * 监听艺术家变更，级联加载专辑
 * @why 只有确定了艺术家，才能列出属于该艺术家的专辑，确保数据一致性。
 */
watch(() => formModel.artist_id, async (newArtistId) => {
  // 清空当前选中的专辑
  formModel.album_id = null;
  albumOptions.value = [];

  if (newArtistId) {
    isAlbumLoading.value = true;
    try {
      const albums = await musicApi.getAlbumsByArtist(newArtistId);
      albumOptions.value = albums.map(a => ({
        label: a.title,
        value: a.id
      }));
    } catch (error) {
      message.error('加载专辑列表失败');
    } finally {
      isAlbumLoading.value = false;
    }
  }
});

// --- Logic: Upload Handling ---

/**
 * 处理文件变更
 * @description 限制只能选择一个文件，且必须是音频
 */
const handleFileChange = (data: { fileList: any[] }) => {
  fileList.value = data.fileList;
  // 简单的自动填充：如果没填标题，使用文件名（去掉后缀）
  if (data.fileList.length > 0 && !formModel.title) {
    const file = data.fileList[0].file;
    if (file && file.name) {
      const name = file.name.replace(/\.[^/.]+$/, "");
      formModel.title = name;
    }
  }
};

/**
 * 提交表单
 * @description 校验表单 -> 校验文件 -> 调用 API
 */
const handleSubmit = (e: MouseEvent) => {
  e.preventDefault();

  formRef.value?.validate(async (errors) => {
    if (errors) return;

    if (fileList.value.length === 0) {
      message.warning('请选择音频文件');
      return;
    }

    const file = fileList.value[0].file;
    if (!formModel.album_id) return; // Should be caught by validate, double check

    loading.value = true;
    try {
      await musicApi.uploadMusic(file, {
        title: formModel.title,
        duration: formModel.duration,
        album_id: formModel.album_id,
        track_number: formModel.track_number
      });

      message.success('上传成功');
      emit('success');
      closeModal();
    } catch (error) {
      // API 层已有错误提示，此处无需重复，除非有特殊处理
    } finally {
      loading.value = false;
    }
  });
};

const closeModal = () => {
  emit('update:show', false);
  // 重置表单
  formModel.title = '';
  formModel.artist_id = null;
  formModel.album_id = null;
  fileList.value = [];
};

// 每次打开模态框时，确保艺术家列表是最新的
watch(() => props.show, (val) => {
  if (val) {
    fetchArtists();
  }
});
</script>

<template>
  <n-modal
      :show="show"
      @update:show="(val) => emit('update:show', val)"
      preset="card"
      title="上传音乐"
      style="width: 600px"
      :mask-closable="false"
  >
    <n-form
        ref="formRef"
        :model="formModel"
        :rules="rules"
        label-placement="left"
        label-width="100"
        require-mark-placement="right-hanging"
    >
      <n-form-item label="歌曲标题" path="title">
        <n-input v-model:value="formModel.title" placeholder="请输入歌曲名"/>
      </n-form-item>

      <n-form-item label="艺术家" path="artist_id">
        <n-select
            v-model:value="formModel.artist_id"
            :options="artistOptions"
            placeholder="请选择艺术家"
            filterable
        />
      </n-form-item>

      <n-form-item label="所属专辑" path="album_id">
        <n-select
            v-model:value="formModel.album_id"
            :options="albumOptions"
            :loading="isAlbumLoading"
            :disabled="!formModel.artist_id"
            placeholder="请先选择艺术家，再选择专辑"
            filterable
        />
      </n-form-item>

      <n-form-item label="音轨号" path="track_number">
        <n-input-number v-model:value="formModel.track_number" :min="1"/>
      </n-form-item>

      <n-form-item label="时长(秒)" path="duration">
        <n-input-number v-model:value="formModel.duration" :min="1" placeholder="暂需手动输入"/>
      </n-form-item>

      <n-form-item label="音频文件">
        <n-upload
            :default-upload="false"
            :max="1"
            accept="audio/*"
            @change="handleFileChange"
            v-model:file-list="fileList"
        >
          <n-button>选择文件</n-button>
        </n-upload>
      </n-form-item>
    </n-form>

    <template #footer>
      <div class="modal-actions">
        <n-button @click="closeModal" :disabled="loading">取消</n-button>
        <n-button type="primary" :loading="loading" @click="handleSubmit">
          确认上传
        </n-button>
      </div>
    </template>
  </n-modal>
</template>

<style scoped>
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>