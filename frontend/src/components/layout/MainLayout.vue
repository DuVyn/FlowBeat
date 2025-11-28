<script setup lang="ts">
import {NLayout, NLayoutSider, NLayoutHeader, NLayoutContent} from 'naive-ui';
import Sidebar from './Sidebar.vue';
import Header from './Header.vue';
// 暂时没有 AudioPlayer，预留插槽
</script>

<template>
  <n-layout position="absolute">
    <n-layout-header style="height: 64px;" bordered>
      <Header/>
    </n-layout-header>

    <n-layout has-sider position="absolute" style="top: 64px; bottom: 0">
      <n-layout-sider
          bordered
          width="240"
          content-style="padding: 24px;"
          :native-scrollbar="false"
      >
        <Sidebar/>
      </n-layout-sider>

      <n-layout-content content-style="padding: 24px;">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component"/>
          </transition>
        </router-view>
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>