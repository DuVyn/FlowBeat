<script setup lang="ts">
import {onMounted, ref, reactive} from 'vue';
import {useUserStore} from '@/stores/userStore.ts';
import {
  NCard,
  NDescriptions,
  NDescriptionsItem,
  NTag,
  NAvatar,
  NButton,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NIcon,
  useMessage,
  type FormInst,
  type FormRules
} from 'naive-ui';
import {Create as EditIcon} from '@vicons/ionicons5';
import apiService from '@/api/axios';

const userStore = useUserStore();
const message = useMessage();

// 编辑模态框状态
const showEditModal = ref(false);
const isSubmitting = ref(false);
const formRef = ref<FormInst | null>(null);

// 编辑表单数据
const editForm = reactive({
  username: '',
  email: '',
  password: ''
});

// 表单验证规则
const formRules: FormRules = {
  username: [
    {required: true, message: '请输入用户名', trigger: 'blur'},
    {min: 2, max: 32, message: '用户名长度应在 2-32 个字符之间', trigger: 'blur'}
  ],
  email: [
    {required: true, message: '请输入邮箱', trigger: 'blur'},
    {type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur'}
  ],
  password: [
    {min: 6, message: '密码长度至少为 6 个字符', trigger: 'blur'}
  ]
};

// 打开编辑模态框
const openEditModal = () => {
  if (userStore.userInfo) {
    editForm.username = userStore.userInfo.username;
    editForm.email = userStore.userInfo.email;
    editForm.password = '';
  }
  showEditModal.value = true;
};

// 提交编辑表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate();
  } catch {
    return;
  }

  isSubmitting.value = true;
  try {
    // 构建更新请求体，仅包含非空字段
    const updateData: Record<string, string> = {};
    if (editForm.username && editForm.username !== userStore.userInfo?.username) {
      updateData.username = editForm.username;
    }
    if (editForm.email && editForm.email !== userStore.userInfo?.email) {
      updateData.email = editForm.email;
    }
    if (editForm.password) {
      updateData.password = editForm.password;
    }

    // 如果没有任何修改，直接关闭
    if (Object.keys(updateData).length === 0) {
      message.info('没有需要更新的内容');
      showEditModal.value = false;
      return;
    }

    // 调用 PATCH /api/v1/users/me 接口
    await apiService.patch('/users/me', updateData);
    message.success('资料更新成功');
    showEditModal.value = false;

    // 刷新用户信息
    await userStore.fetchUserInfo();
  } catch {
    // 错误已由拦截器处理
  } finally {
    isSubmitting.value = false;
  }
};

onMounted(() => {
  // 进入页面时确保数据最新
  if (!userStore.userInfo) {
    userStore.fetchUserInfo();
  }
});
</script>

<template>
  <div class="profile-container">
    <n-card title="个人信息">
      <template #header-extra>
        <n-button type="primary" @click="openEditModal">
          <template #icon>
            <n-icon>
              <EditIcon/>
            </n-icon>
          </template>
          编辑资料
        </n-button>
      </template>

      <div class="avatar-section">
        <n-avatar
            :size="80"
            :src="userStore.userInfo?.avatar_url || undefined"
            fallback-src="https://07akioni.oss-cn-beijing.aliyuncs.com/07akioni.jpeg"
        />
      </div>

      <n-descriptions label-placement="left" bordered :column="1" style="margin-top: 20px;">
        <n-descriptions-item label="用户ID">
          {{ userStore.userInfo?.id }}
        </n-descriptions-item>
        <n-descriptions-item label="用户名">
          {{ userStore.userInfo?.username }}
        </n-descriptions-item>
        <n-descriptions-item label="邮箱">
          {{ userStore.userInfo?.email }}
        </n-descriptions-item>
        <n-descriptions-item label="角色">
          <n-tag :type="userStore.userInfo?.role === 'ADMIN' ? 'error' : 'info'">
            {{ userStore.userInfo?.role }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="账号状态">
          <n-tag :type="userStore.userInfo?.is_active ? 'success' : 'error'">
            {{ userStore.userInfo?.is_active ? '正常' : '禁用' }}
          </n-tag>
        </n-descriptions-item>
      </n-descriptions>
    </n-card>

    <!-- 编辑资料模态框 -->
    <n-modal
        v-model:show="showEditModal"
        preset="card"
        title="编辑资料"
        :style="{width: '400px'}"
        :mask-closable="false"
    >
      <n-form
          ref="formRef"
          :model="editForm"
          :rules="formRules"
          label-placement="left"
          label-width="80"
      >
        <n-form-item label="用户名" path="username">
          <n-input v-model:value="editForm.username" placeholder="请输入用户名"/>
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="editForm.email" placeholder="请输入邮箱"/>
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input
              v-model:value="editForm.password"
              type="password"
              placeholder="留空则不修改密码"
              show-password-on="click"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 12px;">
          <n-button @click="showEditModal = false">取消</n-button>
          <n-button type="primary" :loading="isSubmitting" @click="handleSubmit">
            保存
          </n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<style scoped>
.profile-container {
  max-width: 800px;
  margin: 0 auto;
}

.avatar-section {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}
</style>