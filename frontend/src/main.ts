import {createApp} from 'vue';
import {createPinia} from 'pinia';
import App from './App.vue';
import router from './router';

// 引入通用字体样式 (可选，根据实际需求)
// import 'vfonts/Lato.css' 

const app = createApp(App);

// 挂载 Pinia 状态管理
const pinia = createPinia();
app.use(pinia);

// 挂载 路由
app.use(router);

app.mount('#app');