// 测试看板 API 的脚本
// 在浏览器控制台运行此脚本

console.log('=== 测试看板管理 API ===');

// 1. 检查当前用户权限
const userInfo = JSON.parse(localStorage.getItem('USER_INFO') || '{}');
console.log('用户权限:', userInfo.tenantPermissions);
console.log('包含 board_manage?', userInfo.tenantPermissions?.includes('board_manage'));

// 2. 获取 token
const accessToken = localStorage.getItem('ACCESS_TOKEN');
console.log('Token 存在?', !!accessToken);

// 3. 测试 API 调用
if (accessToken) {
    fetch('http://localhost:8000/api/v1/app/boards', {
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        }
    })
        .then(res => {
            console.log('API 响应状态:', res.status);
            return res.json();
        })
        .then(data => {
            console.log('API 响应数据:', data);
            if (data.code === 200) {
                console.log('✅ API 调用成功，看板数量:', data.data?.boards?.length || 0);
            } else {
                console.error('❌ API 返回错误:', data.msg);
            }
        })
        .catch(err => {
            console.error('❌ API 调用失败:', err);
        });
} else {
    console.error('❌ 未找到 access token，请先登录');
}
