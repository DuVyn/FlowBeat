<script setup lang="ts">
import {NConfigProvider, NMessageProvider, NDialogProvider, NGlobalStyle} from 'naive-ui';
import {useTheme} from '@/composables/useTheme';

const {theme} = useTheme();
</script>

<template>
  <n-config-provider :theme="theme">
    <n-global-style/>
    <n-message-provider>
      <n-dialog-provider>
        <router-view/>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<style>
/* 全局重置样式 */
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
}
</style>