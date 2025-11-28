<script setup lang="ts">
import {onMounted} from 'vue';
import {useUserStore} from '@/stores/userStore.ts';
import {NCard, NDescriptions, NDescriptionsItem, NTag, NAvatar} from 'naive-ui';

const userStore = useUserStore();

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