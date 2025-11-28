<script setup lang="ts">
import {ref, reactive} from 'vue';
import {useRouter} from 'vue-router';
import {authApi} from '@/api/auth';
import {NCard, NForm, NFormItem, NInput, NButton, useMessage, type FormInst, type FormRules} from 'naive-ui';
import type {RegisterRequest} from '@/types/api';

const router = useRouter();
const message = useMessage();
const formRef = ref<FormInst | null>(null);
const loading = ref(false);

const model = reactive<RegisterRequest & { confirmPassword: '' }>({
  email: '',
  username: '',
  password: '',
  confirmPassword: ''
});

// 自定义校验：确认密码
const validatePasswordSame = (_rule: any, value: string) => {
  return value === model.password;
};

const rules: FormRules = {
  email: [
    {required: true, message: '请输入邮箱', trigger: ['blur']},
    {type: 'email', message: '格式不正确', trigger: ['blur']}
  ],
  username: [
    {required: true, message: '请输入用户名', trigger: ['blur']}
  ],
  password: [
    {required: true, message: '请输入密码', trigger: ['blur']},
    {min: 6, message: '至少6位', trigger: ['blur']}
  ],
  confirmPassword: [
    {required: true, message: '请确认密码', trigger: ['blur']},
    {validator: validatePasswordSame, message: '两次密码输入不一致', trigger: ['blur']}
  ]
};

const handleRegister = (e: MouseEvent) => {
  e.preventDefault();
  formRef.value?.validate(async (errors) => {
    if (!errors) {
      loading.value = true;
      try {
        // 调用封装好的 API
        await authApi.register({
          email: model.email,
          username: model.username,
          password: model.password
        });
        message.success('注册成功，请登录');
        router.push('/login');
      } catch (error) {
        // 错误由拦截器处理
      } finally {
        loading.value = false;
      }
    }
  });
};
</script>

<template>
  <div class="auth-container">
    <n-card title="注册 FlowBeat" class="auth-card" size="huge">
      <n-form ref="formRef" :model="model" :rules="rules">
        <n-form-item path="email" label="邮箱">
          <n-input v-model:value="model.email" placeholder="user@example.com"/>
        </n-form-item>
        <n-form-item path="username" label="用户名">
          <n-input v-model:value="model.username" placeholder="给自己起个名字"/>
        </n-form-item>
        <n-form-item path="password" label="密码">
          <n-input type="password" v-model:value="model.password" show-password-on="click"/>
        </n-form-item>
        <n-form-item path="confirmPassword" label="确认密码">
          <n-input type="password" v-model:value="model.confirmPassword" show-password-on="click"/>
        </n-form-item>
      </n-form>

      <div class="actions">
        <n-button type="primary" block :loading="loading" @click="handleRegister">
          注册
        </n-button>
        <div class="footer-links">
          <n-button text @click="router.push('/login')">已有账号？去登录</n-button>
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
}

.auth-card {
  width: 100%;
  max-width: 400px;
}

.actions {
  margin-top: 20px;
}

.footer-links {
  margin-top: 16px;
  text-align: center;
}
</style>