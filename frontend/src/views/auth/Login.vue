<script setup lang="ts">
import {ref, reactive} from 'vue';
import {useRouter} from 'vue-router';
import {useUserStore} from '@/stores/userStore';
import {NCard, NForm, NFormItem, NInput, NButton, useMessage, type FormInst, type FormRules} from 'naive-ui';
import type {LoginRequest} from '@/types/api';

const router = useRouter();
const userStore = useUserStore();
const message = useMessage(); // 使用 Naive UI 的消息钩子

const formRef = ref<FormInst | null>(null);
const loading = ref(false);

const model = reactive<LoginRequest>({
  username: '', // 实际对应邮箱
  password: '',
});

const rules: FormRules = {
  username: [
    {required: true, message: '请输入邮箱', trigger: ['blur', 'input']},
    {type: 'email', message: '请输入有效的邮箱地址', trigger: ['blur', 'input']}
  ],
  password: [
    {required: true, message: '请输入密码', trigger: ['blur', 'input']},
    {min: 6, message: '密码长度至少为 6 位', trigger: ['blur', 'input']}
  ]
};

const handleLogin = (e: MouseEvent) => {
  e.preventDefault();
  formRef.value?.validate(async (errors) => {
    if (!errors) {
      loading.value = true;
      try {
        await userStore.login(model);
        message.success('登录成功，欢迎回来！');
        // 登录成功后跳转到发现页
        router.push('/discovery');
      } catch (error) {
        // 错误已由 axios 拦截器统一处理，此处仅需重置 loading
      } finally {
        loading.value = false;
      }
    }
  });
};

const goToRegister = () => {
  router.push('/register');
};
</script>

<template>
  <div class="auth-container">
    <n-card title="FlowBeat 登录" class="auth-card" size="huge">
      <n-form ref="formRef" :model="model" :rules="rules">
        <n-form-item path="username" label="邮箱">
          <n-input v-model:value="model.username" placeholder="user@example.com"/>
        </n-form-item>
        <n-form-item path="password" label="密码">
          <n-input
              v-model:value="model.password"
              type="password"
              show-password-on="click"
              placeholder="请输入密码"
              @keydown.enter.prevent
          />
        </n-form-item>
      </n-form>

      <div class="actions">
        <n-button type="primary" block :loading="loading" @click="handleLogin">
          登录
        </n-button>
        <div class="footer-links">
          <span>还没有账号？</span>
          <n-button text type="primary" @click="goToRegister">去注册</n-button>
        </div>
      </div>
    </n-card>
  </div>
</template>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
  /* 适配深色模式背景 */
  transition: background-color 0.3s;
}

/* 深色模式下的背景适配通常由全局样式处理，或者使用 Naive UI 的背景色 */

.auth-card {
  width: 100%;
  max-width: 400px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.actions {
  margin-top: 20px;
}

.footer-links {
  margin-top: 16px;
  display: flex;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
}
</style>