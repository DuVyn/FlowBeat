import {ref, computed} from 'vue';
import {darkTheme, type GlobalTheme} from 'naive-ui';

// 定义 LocalStorage Key
const THEME_KEY = 'flowbeat_theme_preference';

export function useTheme() {
    // 初始化状态：优先读取本地存储，默认为 'light'
    // 'dark' 代表深色模式，'light' 代表浅色模式
    const storedTheme = localStorage.getItem(THEME_KEY);
    const isDark = ref(storedTheme === 'dark');

    /**
     * Naive UI 主题对象
     * @description Naive UI 通过传递 null 为浅色，darkTheme 对象为深色
     */
    const theme = computed<GlobalTheme | null>(() => (isDark.value ? darkTheme : null));

    /**
     * 切换主题
     * @description 切换状态并持久化到本地存储
     */
    const toggleTheme = () => {
        isDark.value = !isDark.value;
        localStorage.setItem(THEME_KEY, isDark.value ? 'dark' : 'light');
    };

    return {
        isDark,
        theme,
        toggleTheme,
    };
}