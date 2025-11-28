<script setup lang="ts">
import {h} from 'vue';
import {NButton, NAvatar, NDropdown, NFlex, NText, NIcon, useThemeVars} from 'naive-ui';
import {useUserStore} from '@/stores/userStore';
import {useTheme} from '@/composables/useTheme';
import {LogOutOutline as LogoutIcon, Person as PersonIcon, Moon as MoonIcon, Sunny as SunIcon} from '@vicons/ionicons5';
import {useRouter} from 'vue-router';

const userStore = useUserStore();
const router = useRouter();
const themeVars = useThemeVars();
const {isDark, toggleTheme} = useTheme();

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
</script>

<template>
  <div class="header-container">
    <div class="logo-area">
      <n-text class="logo-text" strong>FlowBeat</n-text>
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