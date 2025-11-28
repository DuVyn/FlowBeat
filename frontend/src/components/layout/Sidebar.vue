<script setup lang="ts">
import {h, ref, watch, type Component} from 'vue';
import {NMenu, NIcon, type MenuOption} from 'naive-ui';
import {RouterLink, useRoute} from 'vue-router';

// 移除未使用的 'MusicalNotes as MusicIcon' 导入，解决 TS6133 报错
// 保持代码整洁，利于 Tree Shaking 减少打包体积
import {
  Person as UserIcon,
  Library as LibraryIcon,
  Compass as DiscoveryIcon
} from '@vicons/ionicons5';

/**
 * 渲染图标的辅助工厂函数
 * * @param icon - Vue 组件 (Ionicons)
 * @returns 渲染函数
 * * @design
 * 使用渲染函数 (Render Function) 而非模板语法的权衡：
 * Naive UI 的 icon 属性需要一个返回 VNode 的函数。
 * 直接传递组件会导致性能损耗，封装为闭包函数可按需渲染。
 */
function renderIcon(icon: Component) {
  return () => h(NIcon, null, {default: () => h(icon)});
}

// 路由实例
const route = useRoute();

/**
 * 菜单状态管理
 * * @design
 * 使用 ref 存储当前高亮的 key。
 * 初始值设为 null，由下方的 watch 立即执行来填充，
 * 避免 setup 执行时路由尚未完全就绪可能导致的 hydration 不匹配问题。
 */
const activeKey = ref<string | null>(null);

/**
 * 菜单配置项
 * * @design
 * 1. Label 使用 RouterLink 包裹：实现 SPA 无刷新跳转，避免整页重载。
 * 2. Key 与 Route Name 保持一致：建立路由与菜单的隐式映射关系。
 */
const menuOptions: MenuOption[] = [
  {
    label: () => h(RouterLink, {to: '/discovery'}, {default: () => '发现'}),
    key: 'discovery', // 对应路由名称
    icon: renderIcon(DiscoveryIcon),
  },
  {
    label: () => h(RouterLink, {to: '/library'}, {default: () => '音乐库'}),
    key: 'library',
    icon: renderIcon(LibraryIcon),
  },
  {
    label: () => h(RouterLink, {to: '/profile'}, {default: () => '个人中心'}),
    key: 'profile',
    icon: renderIcon(UserIcon),
  },
];

/**
 * 路由同步监听 (核心修复)
 * * @why
 * 原代码仅在 setup 时赋值一次，无法响应浏览器后退/前进操作。
 * 使用 watch 配合 { immediate: true } 确保：
 * 1. 初始化时立即高亮当前菜单。
 * 2. 路由变更时自动更新高亮状态。
 */
watch(
    () => route.name,
    (newRouteName) => {
      // 增加边界检查：确保路由名称存在且为字符串
      if (newRouteName && typeof newRouteName === 'string') {
        activeKey.value = newRouteName;
      } else {
        // 可选：处理未知路由的情况，例如清空高亮
        activeKey.value = null;
      }
    },
    {immediate: true}
);
</script>

<template>
  <n-menu
      v-model:value="activeKey"
      :collapsed-width="64"
      :collapsed-icon-size="22"
      :options="menuOptions"
  />
</template>